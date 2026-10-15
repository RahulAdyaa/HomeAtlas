#!/usr/bin/env python3
"""Synthetic PDF generation/citation evaluation with independent real inference runs."""
from __future__ import annotations
import os,sys,json,time,re,statistics,hashlib,math
from importlib.metadata import version as package_version
from pathlib import Path
from dataclasses import replace
from collections import Counter
E=Path(__file__).resolve().parent; EVALUATOR_ROOT=E.parent
ROOT=Path(os.environ.get('EVAL_APP_ROOT',str(EVALUATOR_ROOT))).resolve()
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(E))
os.environ.setdefault('EVAL_SHARED_RUNTIME',str(E/'runtime'))
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['RAGAS_DO_NOT_TRACK']='true'
from protocol import argument_parser,questions,canonical_chunks,relevant_chunk_ids,cache_key as _cache_key,make_result as _make_result,write_result,metric,shared_generation_slot,app_fingerprint as _app_fingerprint,digest
from worker.config import settings
from worker.models import LocalModels
from worker.ingestion import extract
from worker.retrieval import rank_candidates,answer_from_evidence,unrelated_query

# Fingerprints and inference imports must describe the same explicitly selected app.
import worker.models as _worker_module
if Path(_worker_module.__file__).resolve().parents[1] != ROOT:
 raise RuntimeError('Worker imports do not match EVAL_APP_ROOT')
def cache_key(stage,payload,phase,run):return _cache_key(stage,payload,phase,run,root=ROOT)
def app_fingerprint():return _app_fingerprint(ROOT)
def make_result(agent,phase,run,metrics,per_question,config=None):
 return _make_result(agent,phase,run,metrics,per_question,config,root=ROOT)
RUNTIME=E/'runtime'/'generation';RUNTIME.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(RUNTIME/'mpl');(RUNTIME/'mpl').mkdir(exist_ok=True)

def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,default=str,allow_nan=False));tmp.replace(path)
def avg(xs):return statistics.mean(xs) if xs else None
def words(s):return re.findall(r'\w+',s.lower())
def normalized(s):return ' '.join(words(s))
def f1(a,b):
 aa,bb=Counter(words(a)),Counter(words(b));n=sum((aa&bb).values());p=n/max(1,sum(aa.values()));r=n/max(1,sum(bb.values()));return 2*p*r/(p+r) if p+r else 0.
def contains(text,term):return bool(re.search(r'(?<!\w)'+re.escape(str(term).lower())+r'(?!\w)',text.lower()))

class Engine:
 def __init__(self,phase,run,pass_label='main'):
  self.base=LocalModels(replace(settings,storage=RUNTIME,database_url='postgresql://EVALUATION_DISABLED'))
  self.cfg=self.base.cfg;self.status=self.base.status;self.text_identity=self.base.text_identity;self.image_identity=self.base.image_identity;self.phase=phase;self.run=run;self.calls=[];self.usage=[];self.current=None;self.pass_label=pass_label
 def embed_text(self,texts,query=False):
  t=time.perf_counter();v=self.base.embed_text(texts,query);self.calls.append({'stage':'embedding','seconds':time.perf_counter()-t,'cached':False,'question_id':self.current});return v
 def embed_image_space(self,**kw):return self.base.embed_image_space(**kw)
 def rerank(self,q,texts):
  t=time.perf_counter();v=self.base.rerank(q,texts);self.calls.append({'stage':'reranking','seconds':time.perf_counter()-t,'cached':False,'question_id':self.current});return v
 def model_call(self,stage,payload,fn):
  key=cache_key(self.pass_label+'-'+stage,payload,self.phase,self.run);path=RUNTIME/'model_responses'/(key+'.json');t=time.perf_counter()
  if path.exists():
   v=json.loads(path.read_text());cached=True
  else:
   waiting=time.perf_counter()
   with shared_generation_slot():
    wait_seconds=time.perf_counter()-waiting
    global CURRENT_HTTP_ENGINE
    CURRENT_HTTP_ENGINE=self
    locked=time.perf_counter();before=len(self.usage);value=fn();elapsed=time.perf_counter()-locked
   v={'value':value,'seconds':elapsed,'usage':self.usage[before:],'lock_wait_seconds':wait_seconds};save(path,v);cached=False
  self.calls.append({'stage':stage,'seconds':v['seconds'],'wall_seconds':time.perf_counter()-t,'cached':cached,'question_id':self.current,'usage':v.get('usage',[]),'lock_wait_seconds':v.get('lock_wait_seconds')})
  return v['value']
 def generate(self,q,evidence,image=None):return self.model_call('generation',[q,evidence,str(image)],lambda:self.base.generate(q,evidence,image))
 def verify_sections(self,q,sections,evidence):return self.model_call('verification',[q,sections,evidence],lambda:self.base.verify_sections(q,sections,evidence))

def corpus(engine):
 key=digest([app_fingerprint()['app_source_fingerprint'],engine.text_identity,engine.image_identity]);path=RUNTIME/'corpora'/(key+'.json')
 if path.exists():return json.loads(path.read_text())
 manifests=json.loads((E/'fixtures/manifest.json').read_text());qs=questions('pdf');rows=[]
 for manifest in manifests:
  out=RUNTIME/'extracted'/manifest['id'];out.mkdir(parents=True,exist_ok=True)
  chunks=extract(E/manifest['file'],'application/pdf',out,engine.cfg)
  loc=next(q['location_path'] for q in qs if q['modality']==manifest['id'])
  part=canonical_chunks(chunks,manifest['id'],manifest['id']+'.pdf',loc)
  embeddings=engine.embed_text([c['text'] for c in part]);images={}
  for row in part:
   image=row.get('image_path')
   if image and image not in images:images[image]=engine.embed_image_space(image=Path(image))
  for i,row in enumerate(part):row.update(embedding=embeddings[i] if embeddings else None,embedding_model=engine.text_identity if embeddings else None,image_embedding=images.get(row.get('image_path')),image_embedding_model=engine.image_identity if images.get(row.get('image_path')) else None)
  rows.extend(part);print(json.dumps({'event':'ingested','modality':manifest['id'],'chunks':len(part)}),flush=True)
 save(path,rows);return rows

def metrics_for(q,result,candidates,all_rows):
 from rouge_score.rouge_scorer import RougeScorer
 answer=result['answer'];ref=q['reference_answer'];gold=set(relevant_chunk_ids(q,all_rows));lookup={c['id']:c for c in all_rows};citations=result.get('citations',[])
 correct=[];exact=[];page=[];region=[]
 for c in citations:
  canonical=lookup.get(c['id'],{});exact.append(bool(canonical) and c.get('text','') in canonical.get('text',''));correct.append(c['id'] in gold and exact[-1]);page.append(c.get('sourceId')==canonical.get('source_id') and c.get('page')==canonical.get('page') and bool(canonical))
  if q.get('source_regions') and c.get('bbox'):
   import fitz
   region.append(any(fitz.Rect(c['bbox']).intersects(fitz.Rect(b)) for b in q['source_regions']))
 cited_gold={c['id'] for c,good in zip(citations,correct) if good};p=sum(correct)/len(correct) if correct else 0.;rec=len(cited_gold)/len(gold) if gold else None
 termcoverage=avg([float(contains(answer,x)) for x in q.get('evidence_terms',[])]) if not q['unanswerable'] else None
 return {'exact_match':float(normalized(answer)==normalized(ref)),'token_f1':f1(answer,ref),'rouge_l':RougeScorer(['rougeL'],use_stemmer=False).score(ref,answer)['rougeL'].fmeasure,'reference_term_coverage_diagnostic':termcoverage,'citation_gold_precision':p,'citation_gold_recall':rec,'citation_gold_f1':2*p*rec/(p+rec) if rec is not None and p+rec else 0.,'citation_exact_quote_rate':avg([float(x) for x in exact]),'citation_canonical_page_rate':avg([float(x) for x in page]),'citation_authored_region_overlap_rate':avg([float(x) for x in region]),'citation_count':len(citations),'gold_chunk_count':len(gold),'citation_gold_page_recall':len({c.get('page') for c,good in zip(citations,correct) if good}&set(q.get('source_pages',[])))/len(q['source_pages']) if q.get('source_pages') and not q['unanswerable'] else None,'answer_tokens':len(words(answer)),'reference_tokens':len(words(ref)),'abstained':result.get('mode')=='abstention','answer_reference_length_ratio':len(words(answer))/max(1,len(words(ref)))}

def execute(q,all_rows,engine,args):
 key=cache_key(engine.pass_label+'-generation-question',q,args.phase,args.run);path=RUNTIME/'questions'/(key+'.json')
 if path.exists():return json.loads(path.read_text())
 engine.current=q['id'];start=time.perf_counter();before=len(engine.calls);candidates=rank_candidates(q['question'],all_rows,engine);retrieval=time.perf_counter()-start
 # Mirror production adjacent-page expansion and unrelated-query abstention gate.
 selected={c['id'] for c in candidates};neighbors=[]
 for seed in list(candidates):
  for row in all_rows:
   if seed.get('page') is not None and row.get('page') is not None and row['source_id']==seed['source_id'] and row['version_id']==seed['version_id'] and abs(row['page']-seed['page'])<=1 and row['id'] not in selected:selected.add(row['id']);neighbors.append(row)
 candidates=(candidates+neighbors)[:12];t=time.perf_counter()
 rejected=not any(c.get('visual_match') and c.get('image_path') for c in candidates) and unrelated_query(q['question'],candidates)
 result={'answer':"I couldn't find that in your household records.",'citations':[],'confidence':'insufficient','mode':'abstention'} if rejected else answer_from_evidence(q['question'],candidates,engine)
 row={'id':q['id'],'run_id':f'{args.phase}-run-{args.run:02}','inference_pass':engine.pass_label,'suite':q['suite'],'modality':q['modality'],'question':q['question'],'reference_answer':q['reference_answer'],'unanswerable':q['unanswerable'],'type':q['type'],'result':result,'retrieved_ids':[c['id'] for c in candidates],'relevant_ids':relevant_chunk_ids(q,all_rows),'metrics':metrics_for(q,result,candidates,all_rows),'timings':{'retrieval_seconds':retrieval,'generation_seconds':time.perf_counter()-t,'total_seconds':time.perf_counter()-start},'stage_calls':engine.calls[before:]}
 save(path,row);print(json.dumps({'event':'question_complete','id':q['id'],'mode':result.get('mode'),'run':args.run}),flush=True);return row

def reference_embeddings(rows,engine):
 import asyncio
 from ragas.embeddings import BaseRagasEmbeddings
 from ragas.metrics import AnswerSimilarity
 from ragas import SingleTurnSample
 from ragas.run_config import RunConfig
 class AppEmbeddings(BaseRagasEmbeddings):
  def __init__(self):super().__init__();self.set_run_config(RunConfig(max_retries=1))
  def embed_documents(self,texts):return engine.embed_text(texts)
  def embed_query(self,text):return self.embed_documents([text])[0]
  async def aembed_documents(self,texts):return self.embed_documents(texts)
  async def aembed_query(self,text):return self.embed_query(text)
 similarity=AnswerSimilarity(embeddings=AppEmbeddings())
 for row in rows:
  v=engine.embed_text([row['result']['answer'],row['reference_answer']]);row['metrics']['embedding_semantic_similarity']=float(sum(a*b for a,b in zip(*v))) if v else None
  try:row['metrics']['ragas_answer_similarity']=float(asyncio.run(similarity.single_turn_ascore(SingleTurnSample(response=row['result']['answer'],reference=row['reference_answer']))))
  except Exception as exc:row['metrics']['ragas_answer_similarity']=None;row['ragas_answer_similarity_error']=type(exc).__name__
 # Token alignment using the application's local multilingual E5 encoder, explicitly custom BERTScore.
 try:
  from bert_score import BERTScorer
  model_path=Path(engine.cfg.model_dir)/'multilingual-e5-small';cfg=json.loads((model_path/'config.json').read_text());layers=cfg['num_hidden_layers']
  scorer=BERTScorer(model_type=str(model_path),num_layers=layers,batch_size=8,lang='en',rescale_with_baseline=False,device='cpu',idf=False)
  p,r,f=scorer.score([x['result']['answer'] for x in rows],[x['reference_answer'] for x in rows],verbose=False)
  for row,pp,rr,ff in zip(rows,p.tolist(),r.tolist(),f.tolist()):row['metrics'].update(custom_e5_bertscore_precision=pp,custom_e5_bertscore_recall=rr,custom_e5_bertscore_f1=ff)
  return {'model':engine.text_identity,'layers':layers,'idf':False,'rescale_with_baseline':False,'kind':'Custom E5 token alignment, not default English BERTScore benchmark'}
 except Exception as exc:return {'status':'NOT MEASURED','reason':type(exc).__name__}

def summarize(rows,consistency=None):
 out=[];answerable=[r for r in rows if not r['unanswerable']];negative=[r for r in rows if r['unanswerable']];abstain=[r for r in rows if r['metrics']['abstained']]
 keys=['exact_match','token_f1','rouge_l','embedding_semantic_similarity','ragas_answer_similarity','custom_e5_bertscore_precision','custom_e5_bertscore_recall','custom_e5_bertscore_f1','reference_term_coverage_diagnostic','citation_gold_precision','citation_gold_recall','citation_gold_f1','citation_gold_page_recall','citation_exact_quote_rate','citation_canonical_page_rate','citation_authored_region_overlap_rate','answer_reference_length_ratio']
 for k in keys:
  values=[r['metrics'][k] for r in answerable if r['metrics'].get(k) is not None];out.append(metric(k,avg(values),len(values),reason=None if values else 'No applicable observed values'))
 for modality in sorted({r['modality'] for r in rows}):
  subset=[r for r in answerable if r['modality']==modality]
  for k in keys:
   vals=[r['metrics'][k] for r in subset if r['metrics'].get(k) is not None]
   out.append(metric(k+'__'+modality,avg(vals),len(vals),reason=None if vals else 'No applicable observed values'))
 for name,vals in [('abstention_precision',[float(r['unanswerable']) for r in abstain]),('abstention_recall',[float(r['metrics']['abstained']) for r in negative]),('false_refusal_rate',[float(r['metrics']['abstained']) for r in answerable]),('negative_answer_rate',[float(not r['metrics']['abstained']) for r in negative])]:out.append(metric(name,avg(vals),len(vals),reason=None if vals else 'No applicable questions'))
 unavailable=['ragas_faithfulness','ragas_answer_relevancy','ragas_context_precision','ragas_context_recall','ragas_context_entity_recall','ragas_noise_sensitivity','ragas_answer_correctness','ragas_factual_correctness','ragas_multimodal_faithfulness','ragas_multimodal_relevance','answer_completeness_judged','answer_conciseness_judged','claim_groundedness','citation_claim_precision','citation_claim_recall','citation_claim_f1','hallucination_rate']
 out.extend(metric(k,None,len(rows),reason='No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.') for k in unavailable)
 out.append(metric('citation_browser_clickthrough_correct_page_region',None,len(rows),reason='This runner validates canonical citation metadata and exact quotes; no supported browser page/region click-through was executed.'))
 if consistency:
  out.append(metric('consistency_over_three_runs',avg([r['three_way_exact'] for r in consistency]),len(consistency),definition='Exact normalized agreement across three real passes; predeclared first answerable question per modality, n=5.'))
  out.append(metric('three_run_pairwise_token_f1',avg([r['pairwise_token_f1'] for r in consistency]),len(consistency)))
 else:out.append(metric('consistency_over_three_runs',None,0,reason='Third real generation sample is executed after mandatory run2; none observed for this result.'))
 out.append(metric('generation_model_calls',sum(1 for r in rows for c in r['stage_calls'] if c['stage']=='generation' and not c['cached']),len(rows)))
 out.append(metric('verification_model_calls',sum(1 for r in rows for c in r['stage_calls'] if c['stage']=='verification' and not c['cached']),len(rows)))
 return out

def observe_model_artifact(engine,timing):
 """Read-only metadata; an observation does not establish a historical immutable pin."""
 from datetime import datetime,timezone
 from urllib.parse import urlparse
 from urllib.request import urlopen
 observed={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'capture_timing':timing,'requested_model':engine.cfg.generation_model,'endpoint':'configured self-hosted Ollama /api/tags','historical_pin_verified':False}
 try:
  endpoint=urlparse(engine.cfg.ollama_url)
  if endpoint.scheme not in ('http','https') or endpoint.username or endpoint.password:raise ValueError('Invalid model metadata endpoint')
  with urlopen(engine.cfg.ollama_url.rstrip('/')+'/api/tags',timeout=15) as response:data=json.load(response)
  observed['artifacts']=[{k:model.get(k) for k in ['name','model','digest','modified_at']} for model in data.get('models',[]) if engine.cfg.generation_model in (model.get('name'),model.get('model'))]
  observed['status']='MEASURED' if observed['artifacts'] else 'NOT MEASURED'
  if not observed['artifacts']:observed['reason']='Configured tag absent from local model inventory'
 except Exception as exc:observed.update(status='NOT MEASURED',reason=type(exc).__name__)
 return observed

def main():
 global CURRENT_HTTP_ENGINE
 parser=argument_parser(__doc__);args=parser.parse_args();engine=Engine(args.phase,args.run);CURRENT_HTTP_ENGINE=engine
 artifact_before=observe_model_artifact(engine,'before this runner invocation, which may resume same-run cached answers')
 import worker.models as modelmodule
 original=modelmodule.urlopen
 class Response:
  def __init__(self,data):self.data=data
  def __enter__(self):return self
  def __exit__(self,*a):return False
  def read(self):return self.data
 def observed(*a,**kw):
  with original(*a,**kw) as response:data=response.read()
  try:
   content=json.loads(data);usage={k:content.get(k) for k in ['prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration']}
   request_payload=json.loads(a[0].data) if a and getattr(a[0],'data',None) else {}
   usage['input_images']=sum(len(m.get('images',[])) for m in request_payload.get('messages',[]));usage['served_model']=content.get('model');CURRENT_HTTP_ENGINE.usage.append(usage)
  except Exception:pass
  return Response(data)
 modelmodule.urlopen=observed
 rows_corpus=corpus(engine);rows=[]
 for q in questions('pdf'):
  rows.append(execute(q,rows_corpus,engine,args))
  result=make_result('generation-agent',args.phase,args.run,summarize(rows),rows,{'application_root_selection':'EVAL_APP_ROOT' if os.environ.get('EVAL_APP_ROOT') else 'evaluator repository root','call_count_definition':'generation_model_calls and verification_model_calls count new requests represented in final per-question stage records; resumed model-response cache hits retain historical usage/durations and are not new calls. Interrupted predecessor invocations are not reconstructed as new calls.','resource_scheduling':'The shared lock serializes local model requests; other evaluator CPU/embedding work can overlap. Stage wall latency includes lock waiting; model-call seconds exclude it. Development host timings do not establish isolated production capacity.','scope':'Actual worker extraction, canonical prefixed chunks, rank_candidates with visual channel, production adjacency and unrelated-query gate, answer_from_evidence. In-memory corpus; HTTP authorization excluded.','citation_metric_definition':'Gold chunk/page metrics check independently authored source/page annotation and exact canonical quotation; not semantic per-claim support. Claim-level precision/recall/groundedness require a judge and remain unmeasured.','model_artifact_before':artifact_before,'generation_model_requested':engine.cfg.generation_model,'served_generation_models_observed':sorted({u['served_model'] for r in rows for c in r['stage_calls'] for u in c.get('usage',[]) if u.get('served_model')}),'generation_identity_note':'The historical baseline run 1 observer omitted served-model names. They are not inferred from requested tags. Each run lists only HTTP names actually captured.','metric_library_versions':{name:package_version(name) for name in ['ragas','bert-score','rouge-score','numpy','torch','transformers']},'suite':'pdf','requested_n':60,'partial':True,'main_queries_complete':len(rows)==60,'judge_model':None,'judge_reason':'No free-tier judge credential configured','cache_scope':'generation and verification keyed by phase/run/app fingerprint; resumable only within run','observed_models':engine.status})
  write_result(args.output,result)
 bert=reference_embeddings(rows,engine);consistency=[]
 if args.run==2:
  third=Engine(args.phase,args.run,'consistency-third');chosen={'text-01','table-01','image-01','chart-01','scanned-01'}
  for q in questions('pdf'):
   if q['id'] not in chosen:continue
   r3=execute(q,rows_corpus,third,args);r2=next(r for r in rows if r['id']==q['id']);r1path=RUNTIME/'questions'/(cache_key('main-generation-question',q,args.phase,1)+'.json')
   if not r1path.exists():r1path=RUNTIME/'questions'/(cache_key('generation-question',q,args.phase,1)+'.json')
   if not r1path.exists():continue
   r1=json.loads(r1path.read_text());aa=[r['result']['answer'] for r in [r1,r2,r3]]
   consistency.append({'id':q['id'],'run_ids':[r1['run_id'],r2['run_id'],r3['run_id']+'-third-pass'],'third_pass_result':r3,'three_way_exact':float(len({normalized(a) for a in aa})==1),'pairwise_token_f1':avg([f1(aa[0],aa[1]),f1(aa[0],aa[2]),f1(aa[1],aa[2])])})
 result=make_result('generation-agent',args.phase,args.run,summarize(rows,consistency),rows,{**result['config'],'partial':False,'completion':{'main_queries_complete':len(rows)==60,'reference_metrics_complete':True,'consistency_sample_complete':args.run==1 or len(consistency)==5},'custom_bertscore':bert,'model_artifact_after':observe_model_artifact(engine,'after main questions and consistency sample'),'observed_models':engine.status});result['three_run_consistency_sample']=consistency;write_result(args.output,result)
 print(json.dumps({'event':'run_complete','run':args.run,'questions':len(rows)}),flush=True)
if __name__=='__main__':main()
