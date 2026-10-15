import numpy as np
from .common import normalize, ranked, CONFIG

def search(question, documents, engine, limit=30):
    vectors = engine.embed_text([normalize(question)], query=True)
    if not vectors: return []
    q = np.asarray(vectors[0])
    scores = []
    for doc in documents:
        v = doc.get('embedding')
        if v and doc.get('embedding_model') == engine.text_identity and len(v) == len(q):
            score = float(np.dot(q, v)/(max(1e-12,np.linalg.norm(q)*np.linalg.norm(v))))
            if score >= CONFIG['dense_min']: scores.append((doc['id'],score))
    return ranked(scores,limit)
