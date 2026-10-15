"""Auxiliary SigLIP channel. Visual similarity proposes evidence; it never proves a fact."""
import numpy as np
from .common import CONFIG, ranked


def search(question,documents,engine,limit=30,image=None):
    vector=engine.embed_image_space(image=image) if image else engine.embed_image_space(text=question)
    if not vector:return []
    q=np.asarray(vector)
    scores=[]
    for d in documents:
        v=d.get('image_embedding')
        if not v or d.get('image_embedding_model')!=engine.image_identity or len(v)!=len(q):continue
        score=float(np.dot(q,v)/max(1e-12,np.linalg.norm(q)*np.linalg.norm(v)))
        threshold=CONFIG['visual']['image_min'] if image else CONFIG['visual']['text_min']
        if score>=threshold:scores.append((d['id'],score))
    return ranked(scores,limit)
