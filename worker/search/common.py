import json
import re
import unicodedata
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / 'config/retrieval.json').read_text())
ALIASES = json.loads((ROOT / 'config/search-aliases.json').read_text())
STOP = set('which what when where who why how is are was were a an the and or of in on to for my our me does do can you this that it with from about tell show please find locate get give i have kept put stored hai hain mera meri mere ka ki ke batao kya mujhe'.split())

def basic(text):
    text = unicodedata.normalize('NFKC', str(text)).lower()
    # Preserve numbers and legitimate double letters; only collapse 3+ alphabetic runs.
    text = re.sub(r'([^\W\d_])\1{2,}', r'\1\1', text)
    return ' '.join(re.sub(r'[^\w\s]|_', ' ', text).split())

ALIAS_PAIRS = sorted([(basic(alias), basic(key)) for key, values in ALIASES.items()
                      for alias in [key, *values]], key=lambda pair: len(pair[0]), reverse=True)

def normalize(text):
    text = basic(text)
    for alias, key in ALIAS_PAIRS:
        text = re.sub(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', key, text)
    return text

def tokens(text):
    return [w for w in normalize(text).split() if w not in STOP]

def index_text(doc):
    meta = doc.get('metadata') or {}
    raw=' '.join(str(x or '') for x in [doc.get('text'), doc.get('title'),
        doc.get('location_path') or meta.get('location_path'), meta.get('tags'), doc.get('tags')])
    return normalize(raw)+' '+basic(raw)

def edit_distance(a, b):
    """Damerau optimal-string-alignment distance (adjacent transpositions)."""
    rows = [list(range(len(b) + 1))]
    for i, x in enumerate(a, 1):
        row = [i]
        for j, y in enumerate(b, 1):
            n = min(row[-1] + 1, rows[-1][j] + 1, rows[-1][j-1] + (x != y))
            if i > 1 and j > 1 and x == b[j-2] and a[i-2] == y:
                n = min(n, rows[-2][j-2] + 1)
            row.append(n)
        rows.append(row)
    return rows[-1][-1]

@dataclass(frozen=True)
class Hit:
    id: str
    score: float


def ranked(scores, limit):
    return [Hit(str(key), float(score)) for key, score in sorted(scores, key=lambda x: (-x[1], str(x[0]))) if score > 0][:limit]


def index_tokens(doc):
    return [w for w in basic(index_text(doc)).split() if w not in STOP]
