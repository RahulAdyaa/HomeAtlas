"""Actual PostgreSQL channel comparison + local model/cache benchmark, synthetic data only.
Run: worker/.venv/bin/python evaluation/hybrid_eval.py
"""
import sys,json,uuid,time,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from worker.config import settings
from worker.models import LocalModels
from worker.search.common import CONFIG
from worker.search.postgres import channel,params,retrieve
from worker.search.fusion import assemble
from worker.search import cache
from worker.retrieval import answer_from_evidence
from hybrid_testset import DOCUMENTS,QUERIES
from retrieval_metrics import metrics

class MeasuredEngine(LocalModels):
    calls=0
    def generate(self,*a,**kw):
        self.calls+=1
        return super().generate(*a,**kw)

import worker.models as model_module
original_urlopen=model_module.urlopen
llm_calls=0
def counted_urlopen(request,*args,**kwargs):
 global llm_calls
 if request.full_url.endswith('/api/chat'):llm_calls+=1
 return original_urlopen(request,*args,**kwargs)
model_module.urlopen=counted_urlopen
engine=MeasuredEngine();hid=str(uuid.uuid4());uid='hybrid-eval-'+str(uuid.uuid4());mapping={};corpus=[]
root=Path(__file__).resolve().parent
try:
 with psycopg.connect(settings.database_url,row_factory=dict_row) as conn:
  conn.execute('INSERT INTO "user"(id,name,email,"emailVerified","createdAt","updatedAt") VALUES(%s,%s,%s,true,now(),now())',(uid,'Retrieval evaluation',uid+'@example.invalid'))
  conn.execute('INSERT INTO households(id,name,created_by) VALUES(%s,%s,%s)',(hid,'Fictional evaluation',uid))
  conn.execute("INSERT INTO memberships(household_id,user_id,role) VALUES(%s,%s,'owner')",(hid,uid))
 texts=[f'Location: {path}\n{title}. {text}' for _,title,path,text,_ in DOCUMENTS]
 vectors=engine.embed_text(texts)
 if not vectors:raise RuntimeError('Multilingual model unavailable; cannot report vector comparison')
 with psycopg.connect(settings.database_url,row_factory=dict_row) as conn:
  for (key,title,path,text,tags),content,vector in zip(DOCUMENTS,texts,vectors):
   sid,vid,cid=[str(uuid.uuid5(uuid.NAMESPACE_URL,'homeatlas-fictional-eval/'+key+'/'+part)) for part in ['source','version','chunk']];mapping[cid]=key
   conn.execute("INSERT INTO sources(id,household_id,title,mime_type,current_version_id,status,created_by) VALUES(%s,%s,%s,'text/plain',%s,'ready',%s)",(sid,hid,title,vid,uid))
   conn.execute("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES(%s,%s,%s,1,'synthetic-eval','synthetic',1,'text/plain')",(vid,hid,sid))
   conn.execute('INSERT INTO chunks(id,household_id,source_id,version_id,text,embedding,embedding_model,metadata) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(cid,hid,sid,vid,content,vector,engine.text_identity,Jsonb({'tags':tags.split(),'location_path':path})))
 rows=[]
 for i,q in enumerate(QUERIES):
  start=time.perf_counter();scope=params(hid,uid,q['question'],None,None)
  data={name:channel(name,q['question'],scope,settings,engine) for name in ['dense','word','fuzzy']}
  docs={str(d['id']):d for _,ds in data.values() for d in ds};rankings={name:h for name,(h,_) in data.items()}
  hybrid=assemble(q['question'],list(docs.values()),rankings,engine)
  outputs={name:[mapping[h.id] for h in hs[:5]] for name,hs in rankings.items()};outputs['hybrid']=[mapping[str(d['id'])] for d in hybrid]
  rows.append(dict(q,outputs=outputs,metrics={name:metrics(ids,q['relevant'],5) for name,ids in outputs.items()},seconds=time.perf_counter()-start))
  if i%10==0:print('Evaluated',i+1,'queries',flush=True)
 # Cache hit/near-miss benchmark using actual embeddings and real persisted citations.
 ids={v:k for k,v in mapping.items()}
 def reply_for(key):
  with psycopg.connect(settings.database_url,row_factory=dict_row) as c:
   row=c.execute('SELECT c.*,s.location_path,s.title FROM chunks c JOIN sources s ON s.id=c.source_id WHERE c.id=%s',(ids[key],)).fetchone()
  return {'answer':row['text'],'confidence':'supported','mode':'extractive','citations':[{'id':str(row['id']),'sourceId':str(row['source_id']),'versionId':str(row['version_id']),'locationPath':row['location_path'],'text':row['text']}]}
 cache.clear(hid,uid,settings)
 seeds=[('aadhaar','where is my Aadhaar'),('passport','where is my passport'),('fridge','fridge warranty'),('washer','washing machine warranty'),('pan','where is pan')]
 for key,q in seeds:
  m=cache.lookup(hid,uid,q,'',settings,engine)
  cache.store(hid,uid,q,'',m['dataVersion'],reply_for(key),1000,settings,engine)
 variants=[]
 for key,q in seeds:
  for variant in [q,'please locate '+q.replace('where is my ','').replace('where is ',''),'please show '+q.replace('where is my ','').replace('where is ',''),q.replace('my ','our '),q+' please']:
   variants.append((key,variant))
 variants += [('aadhaar','aadhar kahan hai'),('aadhaar','find AAADHAAAR'),('aadhaar','adhar card'),('passport','find my paspsort'),('passport','passprt kahan hai'),('fridge','refrigerator guarantee'),('fridge','frdge warranty'),('washer','washer guarantee'),('washer','washing machien warranty'),('pan','pan card kahan hai')]
 hits=[]
 for target,q in variants:
  t=time.perf_counter();r=cache.lookup(hid,uid,q,'',settings,engine)
  hits.append({'question':q,'hit':r['hit'],'kind':r.get('kind'),'correct':r['hit'] and any(mapping.get(c['id'])==target for c in r['answer']['citations']),'ms':(time.perf_counter()-t)*1000})
 near=['passport photo','passport number','passport in bedroom','passport in study','aadhaar number','pan number','fridge model','washing machine model','fridge warranty kitchen','washing machine warranty laundry','pan card sample','passport sample','passport 123','passport 124','fridge serial number','passport expiry date','fridge receipt','washing machine receipt','pan study','aadhaar living room']
 misses=[{'question':q,'hit':cache.lookup(hid,uid,q,'',settings,engine)['hit']} for q in near]
 # Real generation timing: same prompt twice, cache off vs primed exact cache on.
 q='What is the replacement filter for the air purifier?'
 scope=params(hid,uid,q,None,None)
 ds={name:channel(name,q,scope,settings,engine) for name in ['dense','word','fuzzy']}
 docs={str(d['id']):d for _,rs in ds.values() for d in rs};candidates=assemble(q,list(docs.values()),{n:h for n,(h,_) in ds.items()},engine)
 off=[];modes=[];before=llm_calls
 for _ in range(2):
  t=time.perf_counter();candidates,_=retrieve(q,hid,uid,None,None,settings,engine);reply=answer_from_evidence(q,candidates,engine);off.append((time.perf_counter()-t)*1000);modes.append(reply['mode'])
 off_calls=llm_calls-before
 for c in reply['citations']:
  with psycopg.connect(settings.database_url) as conn:c['locationPath']=conn.execute('SELECT location_path FROM sources WHERE id=%s',(c['sourceId'],)).fetchone()[0]
 m=cache.lookup(hid,uid,q,'',settings,engine);cache.store(hid,uid,q,'',m['dataVersion'],reply,statistics.mean(off),settings,engine)
 on=[];before=llm_calls
 for _ in range(2):
  t=time.perf_counter();r=cache.lookup(hid,uid,q,'',settings,engine);assert r['hit'];on.append((time.perf_counter()-t)*1000)
 timing={'off_mean_ms':statistics.mean(off),'on_mean_ms':statistics.mean(on),'off_generation_calls':off_calls,'on_generation_calls':llm_calls-before,'modes':modes,'scope':'Off measures parallel retrieval + generation/verification; on measures cache lookup. Two repeats with loaded models; cache priming excluded. HTTP/auth/credit accounting excluded.'}
 output={'model':engine.text_identity,'config':CONFIG,'queries':rows,'cache':{'variants':hits,'near_misses':misses,'hit_rate':sum(r['hit'] for r in hits)/len(hits),'false_hit_rate':sum(r['hit'] for r in misses)/len(misses),'timing':timing}}
 (root/'hybrid-results.json').write_text(json.dumps(output,indent=2))
 lines=['# Hybrid retrieval and cache evaluation','',f'Model: `{engine.text_identity}`. Actual PostgreSQL channels, fictional 20-document corpus. No personal records.','',f'{len(QUERIES)} queries, {sum(q["subset"]=="typo" for q in QUERIES)} typo/Hinglish variants; K=5. Gold labels declared in `hybrid_testset.py`.','', '| Subset | Channel | Recall@5 | Precision@5 | MRR@5 | NDCG@5 |','|---|---|---:|---:|---:|---:|']
 summary={}
 for subset in ['overall','typo','identifier']:
  summary[subset]={}
  for channel_name in ['dense','word','fuzzy','hybrid']:
   ms=[r['metrics'][channel_name] for r in rows if r['metrics'][channel_name] and (subset=='overall' or r['subset']==subset)]
   means={k:statistics.mean(v[k] for v in ms) for k in ['recall','precision','mrr','ndcg']};summary[subset][channel_name]=means
   lines.append('| '+subset+' | '+channel_name+' | '+' | '.join(f'{means[k]:.3f}' for k in ['recall','precision','mrr','ndcg'])+' |')
 wins=all(summary['typo']['hybrid']['mrr']>summary['typo'][c]['mrr'] for c in ['dense','word','fuzzy'])
 lines+=['',f'Hybrid strictly beats every single channel on typo MRR: **{wins}**. Ties are not wins. This small synthetic corpus can saturate recall; shared aliases help all channels. We do not alter gold labels or claim production accuracy from this benchmark.','', '## No-match retrieval','', '| Channel | Empty top-5 rate |','|---|---:|']
 for c in ['dense','word','fuzzy','hybrid']:
  ns=[r for r in rows if r['subset']=='no-match'];lines.append(f'| {c} | {sum(not r["outputs"][c] for r in ns)/len(ns):.1%} |')
 lines+=['','Retrieval candidates are not answers: the evidence verifier must abstain when a retrieved record does not answer the question. No-match retrieval failures are explicitly retained in the results.','', '## Semantic cache','',f'Variant hit rate: **{output["cache"]["hit_rate"]:.1%}** ({len(hits)} queries, target ≥90%). Near-miss false-hit rate: **{output["cache"]["false_hit_rate"]:.1%}** ({len(misses)} queries, target <2%).', '', '| Mode | Mean latency (ms) | Generation calls |','|---|---:|---:|',f'| Cache off | {timing["off_mean_ms"]:.1f} | {off_calls} |',f'| Primed cache on | {timing["on_mean_ms"]:.1f} | {timing["on_generation_calls"]} |','',timing['scope'],f'Generation modes: {modes}. Calls count actual local LLM HTTP requests, including evidence verification.','', 'Automated DB tests separately check move/delete freshness, stale writes, user/household isolation, bypass, expiry and LRU. Cache guard intentionally prefers misses for uncertain spellings; threshold remains 0.93. Low semantic similarity or unmatched key terms explain variant misses; inspect the JSON for individual cases.']
 (root/'HYBRID_EVALUATION_REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'summary':summary,'cache_hit_rate':output['cache']['hit_rate'],'false_hit_rate':output['cache']['false_hit_rate'],'timing':timing}),flush=True)
finally:
 with psycopg.connect(settings.database_url) as conn:
  conn.execute('DELETE FROM households WHERE id=%s',(hid,));conn.execute('DELETE FROM "user" WHERE id=%s',(uid,))
