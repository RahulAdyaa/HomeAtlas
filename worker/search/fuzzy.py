"""3–4 character TF-IDF cosine plus conservative token edit-distance fallback."""
import math
from collections import Counter
from .common import tokens, basic, STOP, normalize, index_tokens, index_text, edit_distance, ranked, CONFIG

def grams(text):
    return Counter(g for word in basic(text).split() if word not in STOP for n in (3, 4)
                   for g in [word[i:i+n] for i in range(max(0, len(word)-n+1))])

def search(question, documents, engine=None, limit=30):
    q = grams(normalize(question))
    ds = [grams(index_text(d)) for d in documents]
    idf = {g: math.log((len(ds)+1)/(1+sum(g in d for d in ds)))+1 for g in q}
    qv = {g: count*idf[g] for g, count in q.items()}
    qnorm = math.sqrt(sum(v*v for v in qv.values())) or 1
    scores = []
    qt = tokens(question)
    for doc, d in zip(documents, ds):
        dv = {g: count*idf.get(g, 1) for g, count in d.items()}
        cosine = sum(v*dv.get(g, 0) for g, v in qv.items()) / (qnorm*(math.sqrt(sum(v*v for v in dv.values())) or 1))
        words = set(index_tokens(doc))
        def match(w):
            if w in words: return 1.0
            if len(w)==3:
                return .8 if any(len(v)==3 and sorted(v)==sorted(w) and edit_distance(w,v)==1 for v in words) else 0.0
            if len(w) < 4 or any(c.isdigit() for c in w): return 0.0
            return max((1-edit_distance(w, v)/max(len(w),len(v)) for v in words
                        if abs(len(w)-len(v)) <= 2 and not any(c.isdigit() for c in v)), default=0)
        edit = sum(m if (m := match(w)) >= .75 else 0 for w in qt)/max(1,len(qt))
        title=set(tokens(doc.get('title','')))
        title_bonus=.1*len(set(qt)&title)/max(1,len(title))
        score = max(cosine, edit)+title_bonus
        scores.append((doc['id'], score if score >= CONFIG['fuzzy_min'] else 0))
    return ranked(scores, limit)
