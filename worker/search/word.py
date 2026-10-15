"""BM25 word scoring. PostgreSQL tsvector supplies the production candidate pool."""
import math
from collections import Counter
from .common import tokens, index_text, index_tokens, ranked

def search(question, documents, engine=None, limit=30):
    query = set(tokens(question))
    docs = [index_tokens(d) for d in documents]
    average = max(1, sum(map(len, docs)) / max(1, len(docs)))
    frequency = {w: sum(w in d for d in docs) for w in query}
    scores = []
    for doc, words in zip(documents, docs):
        count = Counter(words)
        score = sum(math.log(1 + (len(docs)-frequency[w]+.5)/(frequency[w]+.5)) * count[w] * 2.2 /
                    (count[w]+1.2*(.25+.75*len(words)/average)) for w in query)
        scores.append((doc['id'], score))
    return ranked(scores, limit)
