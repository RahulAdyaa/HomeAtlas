from concurrent.futures import ThreadPoolExecutor
from . import dense, word, fuzzy
from .common import CONFIG, tokens, normalize

CHANNELS = {'dense': dense.search, 'word': word.search, 'fuzzy': fuzzy.search}

def fuse(rankings, config=CONFIG):
    scores = {}
    for channel, hits in rankings.items():
        seen = set()
        for rank, hit in enumerate(hits, 1):
            if hit.id in seen: continue
            seen.add(hit.id)
            scores[hit.id] = scores.get(hit.id,0) + config['weights'].get(channel,1)/(config['rrf_k']+rank)
    return scores

def retrieve(question, documents, engine, config=CONFIG, channels=None):
    numeric={w for w in tokens(question) if any(c.isdigit() for c in w)}
    from .common import index_text
    documents=[d for d in documents if numeric.issubset(set(tokens(index_text(d))))]
    channels = channels or CHANNELS
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(fn, question, documents, engine, config['channel_top_k']) for name, fn in channels.items()}
        rankings = {name: future.result() for name, future in futures.items()}
    return assemble(question,documents,rankings,engine,config)

def assemble(question,documents,rankings,engine,config=CONFIG):
    scores = fuse(rankings,config)
    query = set(tokens(question))
    by_id = {str(d['id']):d for d in documents}
    results = []
    for key, score in scores.items():
        doc = dict(by_id[key])
        path = doc.get('location_path') or (doc.get('metadata') or {}).get('location_path','')
        location = set(tokens(path))
        boost = len(location & query)/max(1,len(location))
        doc.update(fusion_score=score, relevance=score*(1+config['location_boost']*boost),
                   lexical_score=next((h.score for h in rankings.get('word',[]) if h.id==key),0),
                   fuzzy_score=next((h.score for h in rankings.get('fuzzy',[]) if h.id==key),0),
                   image_score=next((h.score for h in rankings.get('visual',[]) if h.id==key),0),
                   visual_match=any(h.id==key for h in rankings.get('visual',[])),
                   dense_score=next((h.score for h in rankings.get('dense',[]) if h.id==key),0))
        results.append(doc)
    results.sort(key=lambda d:(-d['relevance'],str(d['id'])))
    if config['reranker_enabled'] and results:
        head = results[:config['reranker_top_k']]
        reranked = engine.rerank(question,[d['text'] for d in head])
        if reranked is not None:
            for doc, score in zip(head,reranked): doc['relevance']=score
            results=sorted(head,key=lambda d:-d['relevance'])+results[len(head):]
    return results[:config['top_n']]
