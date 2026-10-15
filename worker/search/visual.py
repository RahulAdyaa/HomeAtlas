"""Auxiliary SigLIP channel. Visual similarity proposes evidence; it never proves a fact."""
import numpy as np
from .common import CONFIG, ranked


def page_key(row):
    """A page preview is repeated on OCR chunks; it is one visual candidate."""
    path = row.get('image_path')
    return (str(row.get('source_id')), str(row.get('version_id')), row.get('page'), path) if path else ('chunk', str(row['id']))


def representatives(rows):
    pages = {}
    for row in rows:
        key = page_key(row)
        # Context chunks preserve labels beside their values. A long native-text
        # chunk is the next best anchor, rather than an arbitrary OCR line.
        priority = lambda d: (bool((d.get('metadata') or {}).get('ocr_context')), len(d.get('text', '')), str(d['id']))
        if key not in pages or priority(row) > priority(pages[key]):
            pages[key] = row
    return list(pages.values())


def search(question,documents,engine,limit=30,image=None):
    vector=engine.embed_image_space(image=image) if image else engine.embed_image_space(text=question)
    if not vector:return []
    q=np.asarray(vector)
    scores=[]
    for d in representatives(documents):
        v=d.get('image_embedding')
        if not v or d.get('image_embedding_model')!=engine.image_identity or len(v)!=len(q):continue
        score=float(np.dot(q,v)/max(1e-12,np.linalg.norm(q)*np.linalg.norm(v)))
        threshold=CONFIG['visual']['image_min'] if image else CONFIG['visual']['text_min']
        if score>=threshold:scores.append((d['id'],score))
    return ranked(scores,limit)
