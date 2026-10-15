#!/usr/bin/env python3
"""Frozen synthetic benchmark of the application's production PostgreSQL retrievers.
No answer generation, customer source reads, or application mutations. Disposable
household fixtures are always removed. Run independently with --run 1 and --run 2.
"""
from __future__ import annotations
import sys, os, json, math, time, statistics, uuid, random
from pathlib import Path
from dataclasses import replace
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation'))
from protocol import (argument_parser, frozen_dataset, questions, canonical_chunks,
                      relevant_chunk_ids, metric, make_result, write_result, SEED)
from dotenv import load_dotenv
MAIN=Path(os.environ.get('EVAL_APP_ROOT',str(ROOT)))
# Local environment is loaded privately; neither keys nor URLs are recorded.
load_dotenv(MAIN/'.env.local',override=False)
os.environ.setdefault('MODEL_DIR',str(MAIN/'data/models'))
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import numpy as np
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from worker.config import settings
from worker.models import LocalModels
from worker.ingestion import extract, ocr_image
from worker.search.common import CONFIG
from worker.search.postgres import channel,params
from worker.search.fusion import assemble
from worker.retrieval import rank_candidates

K_VALUES=(1,3,5,10)

def scores(ids,gold,k):
    if not gold:return None
    r=set(gold);hits=[int(i in r) for i in ids[:k]]
    found=len(set(ids[:k])&r);p=found/k;rec=found/len(r)
    dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits))
    ideal=sum(1/math.log2(i+2) for i in range(min(k,len(r))))
    ap=sum(sum(hits[:i+1])/(i+1) for i,h in enumerate(hits) if h)/len(r)
    return dict(precision=p,recall=rec,f1=2*p*rec/(p+rec) if p+rec else 0,
                hit=float(found>0),mrr=next((1/(i+1) for i,h in enumerate(hits) if h),0),
                ndcg=dcg/ideal if ideal else 0,map=ap,
                r_precision=len(set(ids[:min(k,len(r))])&r)/len(r))

class MeasuredEngine(LocalModels):
    def __init__(self,cfg):
        super().__init__(cfg);self.calls=Counter()
    def embed_text(self,*args,**kw):
        self.calls['text_query' if kw.get('query') else 'text_index']+=1
        return super().embed_text(*args,**kw)
    def embed_image_space(self,*args,**kw):
        self.calls['visual_query' if kw.get('text') is not None else 'visual_index']+=1
        return super().embed_image_space(*args,**kw)
    def rerank(self,*args,**kw):
        self.calls['rerank']+=1;return super().rerank(*args,**kw)

def corpus(engine,runtime):
    manifests=json.loads((ROOT/'evaluation/fixtures/manifest.json').read_text())
    qs=questions('pdf');out=[]
    for m in manifests:
        path=next(q['location_path'] for q in qs if q['modality']==m['id'] and q['location_path'])
        extracted=extract(ROOT/'evaluation'/m['file'],'application/pdf',runtime/m['id'],engine.cfg)
        out+=canonical_chunks(extracted,m['id'],m['id']+'.pdf',path)
        print('retrieval ingestion',m['id'],'chunks',len(extracted),flush=True)
    for d in json.loads((ROOT/'evaluation/scenarios.json').read_text())['documents']:
        row=canonical_chunks([dict(text=d['text'],page=None,modality='text',metadata={})],d['key'],d['title'],d['location_path'],d['tags'])[0]
        row.update(id=d['chunk_id'],source_id=d['id'],fixture_source_id=d['key'],source_modality='household')
        out.append(row)
    embeddings=engine.embed_text([r['text'] for r in out])
    if not embeddings:raise RuntimeError('Pinned dense model unavailable')
    images={}
    for row,vector in zip(out,embeddings):
        row.update(embedding=vector,embedding_model=engine.text_identity)
        image=row.get('image_path')
        if image and image not in images:images[image]=engine.embed_image_space(image=Path(image))
        row.update(image_embedding=images.get(image),image_embedding_model=engine.image_identity if images.get(image) else None)
    return out

class Tenant:
    def __init__(self,cfg,rows):
        self.cfg=cfg;self.rows=rows;self.hid=str(uuid.uuid4());self.uid='retrieval-eval-'+str(uuid.uuid4())
    def __enter__(self):
        try:
            with psycopg.connect(self.cfg.database_url,row_factory=dict_row) as c:
                c.execute('INSERT INTO "user"(id,name,email,"emailVerified","createdAt","updatedAt") VALUES(%s,%s,%s,true,now(),now())',(self.uid,'Synthetic retrieval evaluation',self.uid+'@example.invalid'))
                c.execute('INSERT INTO households(id,name,created_by) VALUES(%s,%s,%s)',(self.hid,'Synthetic retrieval evaluation',self.uid))
                c.execute("INSERT INTO memberships(household_id,user_id,role) VALUES(%s,%s,'owner')",(self.hid,self.uid))
                paths={};sources={}
                for r in self.rows:
                    parts=r['location_path'].split(' > ');parent=self.hid
                    for i,name in enumerate(parts):
                        path=' > '.join(parts[:i+1])
                        if path not in paths:
                            lid=str(uuid.uuid4())
                            if i==0:c.execute('INSERT INTO rooms(id,household_id,name) VALUES(%s,%s,%s)',(lid,self.hid,name))
                            else:c.execute('INSERT INTO locations(id,household_id,name,type,parent_id) VALUES(%s,%s,%s,%s,%s)',(lid,self.hid,name,'zone' if i==1 else 'container',parent))
                            paths[path]=lid
                        parent=paths[path]
                    if r['source_id'] not in sources:
                        c.execute("INSERT INTO sources(id,household_id,title,mime_type,current_version_id,status,created_by,location_id) VALUES(%s,%s,%s,'application/pdf',%s,'ready',%s,%s)",(r['source_id'],self.hid,r['title'],r['version_id'],self.uid,parent))
                        c.execute("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES(%s,%s,%s,1,'synthetic-eval','synthetic',1,'application/pdf')",(r['version_id'],self.hid,r['source_id']))
                        sources[r['source_id']]=True
                    c.execute('INSERT INTO chunks(id,household_id,source_id,version_id,text,page,bbox,modality,embedding,embedding_model,image_path,metadata,image_embedding,image_embedding_model) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (r['id'],self.hid,r['source_id'],r['version_id'],r['text'],r.get('page'),Jsonb(r.get('bbox')),r.get('modality','text'),r['embedding'],r['embedding_model'],r.get('image_path'),Jsonb(r['metadata']),r.get('image_embedding'),r.get('image_embedding_model')))
            return self
        except Exception:
            self.__exit__(None,None,None);raise
    def __exit__(self,*args):
        with psycopg.connect(self.cfg.database_url) as c:
            c.execute('DELETE FROM households WHERE id=%s',(self.hid,))
            c.execute('DELETE FROM "user" WHERE id=%s',(self.uid,))

def run_question(q,tenant,engine,corpus_lookup):
    started=time.perf_counter();scope=params(tenant.hid,tenant.uid,q['question'],None,None)
    names=['dense','word','fuzzy']+(['visual'] if CONFIG.get('visual',{}).get('enabled') else [])
    def timed(name):
        t=time.perf_counter();value=channel(name,q['question'],scope,engine.cfg,engine)
        return value,time.perf_counter()-t
    with ThreadPoolExecutor(max_workers=4) as executor:
        fs={n:executor.submit(timed,n) for n in names};data={n:f.result() for n,f in fs.items()}
    rankings={n:d[0][0] for n,d in data.items()}
    docs={str(d['id']):d for value,_ in data.values() for d in value[1]}
    for id,row in docs.items():
        row.update(source_modality=corpus_lookup[id]['source_modality'])
    outputs={n:[h.id for h in hs[:10]] for n,hs in rankings.items()}
    base={**CONFIG,'top_n':10,'reranker_enabled':False}
    def fused(ranks,config):return [str(r['id']) for r in assemble(q['question'],list(docs.values()),ranks,engine,config)]
    text_ranks={n:r for n,r in rankings.items() if n!='visual'}
    outputs['hybrid_text_diagnostic10']=fused(text_ranks,base)
    outputs['hybrid_runtime']=fused(rankings,CONFIG)
    outputs['hybrid_diagnostic10']=fused(rankings,base)
    for k in (10,30,60,100):
        for weighted in (False,True):
            cfg={**base,'rrf_k':k,'weights':CONFIG['weights'] if weighted else {n:1 for n in names}}
            outputs[f'rrf_{k}_'+('configured_weights' if weighted else 'equal_weights')]=fused(rankings,cfg)
    outputs['reranked_diagnostic10']=fused(rankings,{**base,'reranker_enabled':True})
    gold=relevant_chunk_ids(q,list(corpus_lookup.values()))
    measured={n:{str(k):scores(ids,gold,k) for k in K_VALUES} for n,ids in outputs.items()}
    mix={n:{str(k):dict(Counter(corpus_lookup[i]['source_modality'] for i in ids[:k])) for k in K_VALUES} for n,ids in outputs.items()}
    return dict(id=q['id'],suite=q['suite'],modality=q['modality'],subset=q.get('subset',q['type']),type=q['type'],
        unanswerable=q['unanswerable'],history_supported=not bool(q.get('history')),gold_ids=gold,
        rankings=outputs,metrics=measured,modality_mix=mix,
        channel_scores={n:[{'id':h.id,'score':float(h.score)} for h in hs] for n,hs in rankings.items()},
        timings={'total_seconds':time.perf_counter()-started,**{n:t for n,(_,t) in data.items()}},
        actual_counts={n:len(ids) for n,ids in outputs.items()})

def aggregate(rows,lookup):
    out=[];variants=list(rows[0]['rankings'])
    groups={'all':rows,'pdf':[r for r in rows if r['suite']=='pdf'],'household':[r for r in rows if r['suite']=='household'],
            'typo':[r for r in rows if r['subset']=='typo'],'cross_modal':[r for r in rows if r['type']=='cross-modal']}
    groups.update({m:[r for r in rows if r['modality']==m] for m in sorted({r['modality'] for r in rows})})
    for group,rs in groups.items():
        for variant in variants:
            for k in K_VALUES:
                vals=[r['metrics'][variant][str(k)] for r in rs if r['gold_ids']]
                for field in ['precision','recall','f1','hit','mrr','ndcg','map','r_precision']:
                    out.append(metric(f'{group}/{variant}/{field}@{k}',statistics.mean(v[field] for v in vals) if vals else None,len(vals),reason=None if vals else 'No answerable questions in subset'))
                found=[len(set(r['rankings'][variant][:k])) for r in rs]
                out.append(metric(f'{group}/{variant}/returned_count@{k}',statistics.mean(found) if found else None,len(found),reason=None if found else 'Empty subset'))
            negatives=[r for r in rs if r['unanswerable']]
            out.append(metric(f'{group}/{variant}/empty_candidate_rate',statistics.mean(not r['rankings'][variant] for r in negatives) if negatives else None,len(negatives),reason=None if negatives else 'No unanswerable questions in subset'))
    for k in K_VALUES:
        vals=[];entropy=[];modhits=[]
        for row in rows:
            ids=row['rankings']['hybrid_runtime'][:k]
            if ids:
                vals.append(len({lookup[i]['source_id'] for i in ids})/len(ids))
                counts=Counter(lookup[i]['source_modality'] for i in ids)
                entropy.append(-sum((n/len(ids))*math.log2(n/len(ids)) for n in counts.values()))
            if row['gold_ids']:
                goldmods={lookup[i]['source_modality'] for i in row['gold_ids']}
                modhits.append(float(any(lookup[i]['source_modality'] in goldmods for i in ids)))
        for field,v in [('unique_source_ratio',vals),('modality_entropy',entropy),('gold_modality_hit',modhits)]:
            out.append(metric(f'all/hybrid_runtime/{field}@{k}',statistics.mean(v) if v else None,len(v),reason=None if v else 'No results'))
    return out

def robustness(engine,rows,corpus_rows,runtime):
    import fitz
    from PIL import Image,ImageFilter
    result=[]
    # Each image is a rendered, frozen fixture page; no private uploads are read.
    for modality in ['text','table','image','chart','scanned']:
        row=next(r for r in corpus_rows if r['fixture_source_id']==modality and r.get('page')==1 and r.get('image_path'))
        path=Path(row['image_path']);ocr=' '.join(c.text for c in ocr_image(Image.open(path),engine.cfg))
        found=rank_candidates('Find the record shown in this photo. '+ocr[:1500],corpus_rows,engine,image=path)
        result.append(dict(id='image-query-'+modality,kind='image-query',modality=modality,retrieved_ids=[str(c['id']) for c in found],source_page_hit=float(any(c['source_id']==row['source_id'] and c.get('page')==1 for c in found)),text_modality_hit=float(any(c['source_id']==row['source_id'] and c.get('page')==1 and c.get('modality')=='text' for c in found))))
    src=next(r for r in corpus_rows if r['fixture_source_id']=='scanned' and r.get('page')==1)
    with Image.open(src['image_path']) as pic:base=pic.convert('RGB')
    rng=np.random.default_rng(SEED)
    blurred=base.filter(ImageFilter.GaussianBlur(3));arr=np.asarray(blurred).astype(np.int16)
    variants={'low_resolution':base.resize((300,375)).resize(base.size),'rotated_90':base.rotate(90,expand=True),
              'blur_noise':Image.fromarray(np.clip(arr+rng.normal(0,22,arr.shape),0,255).astype(np.uint8))}
    for name,img in variants.items():
        path=runtime/(name+'.pdf');doc=fitz.open();page=doc.new_page(width=600,height=750)
        import io
        buf=io.BytesIO();img.save(buf,format='PNG');page.insert_image(page.rect,stream=buf.getvalue());doc.save(path);doc.close()
        cs=canonical_chunks(extract(path,'application/pdf',runtime/name,engine.cfg),'scan-variant-'+name,'scanned.pdf',src['location_path'])
        vecs=engine.embed_text([c['text'] for c in cs]);ivs={}
        for c,v in zip(cs,vecs):
            p=c.get('image_path')
            if p and p not in ivs:ivs[p]=engine.embed_image_space(image=Path(p))
            c.update(embedding=v,embedding_model=engine.text_identity,image_embedding=ivs.get(p),image_embedding_model=engine.image_identity if ivs.get(p) else None)
        modified=[r for r in corpus_rows if not(r['fixture_source_id']=='scanned' and r.get('page')==1)]+cs
        for q in questions('pdf'):
            if q['id'] not in ['scanned-01','scanned-02']:continue
            found=rank_candidates(q['question'],modified,engine)
            ids=[str(c['id']) for c in found];gold=[c['id'] for c in cs]
            result.append(dict(id=q['id']+'-'+name,kind='degraded_scan',variant=name,question_id=q['id'],retrieved_ids=ids,gold_ids=gold,metrics=scores(ids,gold,5),baseline_metrics=next(r['metrics']['hybrid_runtime']['5'] for r in rows if r['id']==q['id'])))
    return result

def main():
    args=argument_parser(__doc__).parse_args();frozen_dataset();random.seed(SEED);np.random.seed(SEED)
    runtime=Path(os.environ.get('EVAL_SHARED_RUNTIME',str(MAIN/'evaluation/runtime')))/'retrieval'/f'{args.phase}-run-{args.run:02}'
    runtime.mkdir(parents=True,exist_ok=True)
    cfg=replace(settings,storage=runtime,model_dir=Path(os.environ['MODEL_DIR']))
    engine=MeasuredEngine(cfg);start=time.perf_counter();data=corpus(engine,runtime);lookup={c['id']:c for c in data};qs=questions()
    # Persist only synthetic extraction, with vectors retained in ignored runtime artifacts.
    (runtime/'corpus.json').write_text(json.dumps(data,default=str))
    rows=[]
    with Tenant(cfg,data) as tenant:
        for i,q in enumerate(qs):
            row=run_question(q,tenant,engine,lookup);row['run_id']=f'{args.phase}-run-{args.run:02}';rows.append(row)
            if i%10==0:print('retrieval evaluated',i+1,'of',len(qs),flush=True)
    robust=robustness(engine,rows,data,runtime);metrics=aggregate(rows,lookup)
    for field in ['source_page_hit','text_modality_hit']:
        vals=[r[field] for r in robust if r['kind']=='image-query'];metrics.append(metric('cross_modal/'+field+'@5',statistics.mean(vals),len(vals)))
    scan=[r for r in robust if r['kind']=='degraded_scan']
    for field in ['recall','mrr','hit']:
        metrics.append(metric('degraded_scan/'+field+'@5',statistics.mean(r['metrics'][field] for r in scan),len(scan)))
    # Variant retrieval consistency: report successful variants, and pairwise top-1 equality within authored document groups.
    typos=[r for r in rows if r['subset']=='typo'];groups=defaultdict(list)
    for row in typos:groups[tuple(row['gold_ids'])].append(row)
    pairs=[float(a['rankings']['hybrid_runtime'][:1]==b['rankings']['hybrid_runtime'][:1]) for rs in groups.values() for i,a in enumerate(rs) for b in rs[i+1:]]
    metrics.append(metric('typo/pairwise_top1_consistency',statistics.mean(pairs),len(pairs)))
    metrics.append(metric('paraphrase/independent_paraphrase_set',None,0,reason='Frozen dataset contains typo/Hinglish variants but no separately labeled paraphrase subset; no new gold questions introduced after freeze.'))
    metrics.append(metric('reranker/available',int(not engine.status.get('reranker','unavailable').startswith('unavailable')),len(qs)))
    result=make_result('retrieval-agent',args.phase,args.run,metrics,rows,config={
        'application':CONFIG,'runtime_top_n':CONFIG['top_n'],'diagnostic_top_n':10,'corpus_chunks':len(data),'questions':len(qs),
        'retrieval_backend':'actual worker.search.postgres.channel; concurrent independent channel connections; actual worker.search.fusion.assemble',
        'normalization':'application index triggers and module normalization, unmodified',
        'sensitivity_weights_note':'Configured weights are all 1.0; configured and equal weight tests coincide by design.',
        'r_precision_definition':'R-Precision@K uses relevant hits in first min(K,R) divided by R; standard R-Precision when K>=R.',
        'map_definition':'AP@K denominator is total gold chunk count R, macro averaged over answerable queries.',
        'precision_definition':'Relevant distinct chunks divided by requested K; fewer candidates remain missing slots.',
        'history_policy':'Only current question passed to stateless retrieval, history-bearing follow-up failures retained.',
        'gold_policy':'All extracted chunks on gold pages are relevant; source/page retrieval does not prove textual answer availability.',
        'model_calls':dict(engine.calls),'elapsed_seconds':time.perf_counter()-start,
        'corpus_manifest':[{key:c.get(key) for key in ['id','source_id','fixture_source_id','source_modality','page','modality','location_path']} for c in data],
        'execution_context':'Local shared host; encoders and other evaluators can contend for memory/CPU. Run timings are observed mixed-load diagnostics, not causal production latency comparisons.',
        'synthetic_only':True,'inference_replayed_from_other_run':False,'robustness':robust,
        'defect_policy':'No app logic/config/gold changes; actual production top5 preserved.'},root=ROOT)
    result['models']['observed']=dict(engine.status);result['models']['text_identity']=engine.text_identity;result['models']['image_identity']=engine.image_identity
    write_result(args.output,result)
    print(json.dumps({'completed':result['run_id'],'questions':len(rows),'metrics':len(metrics),'model_status':engine.status}),flush=True)
if __name__=='__main__':main()
