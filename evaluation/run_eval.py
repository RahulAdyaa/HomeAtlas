#!/usr/bin/env python3
"""Read-only application evaluation. All artifacts and caches stay in this directory."""
import os,sys
from pathlib import Path
E=Path(__file__).resolve().parent; APP=E.parent
os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
if Path(sys.prefix).resolve()!= (E/'.venv').resolve():
 p=E/'.venv/bin/python'
 if not p.exists(): raise SystemExit('Run the README setup once to create evaluation/.venv.')
 os.execv(str(p),[str(p),str(__file__),*sys.argv[1:]])
os.environ['RAGAS_DO_NOT_TRACK']='true';os.environ['ANONYMIZED_TELEMETRY']='false'
os.environ['TMPDIR']=str(E/'runtime/tmp');os.environ['MPLCONFIGDIR']=str(E/'runtime/mpl')
(E/'runtime/tmp').mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(APP))
import argparse,json,hashlib,time,random,math,statistics,csv,re,io,asyncio
from dataclasses import asdict,replace
from collections import Counter
import numpy as np
import fitz
from PIL import Image,ImageFilter
from worker.config import settings
from worker.ingestion import extract
from worker.models import LocalModels
from worker.retrieval import rank_candidates,answer_from_evidence,ocr_image
from build_testset import build,raster,png
SEED=741;random.seed(SEED);np.random.seed(SEED)
CACHE=E/'cache';CACHE.mkdir(exist_ok=True)
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False,default=str));t.replace(p)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def mean(x):
 x=[v for v in x if v is not None];return sum(x)/len(x) if x else None
def norm(s):return ' '.join(str(s).lower().split())
def words(s):return re.findall(r'\w+',norm(s))
def edit(a,b):
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  curr=[i]
  for j,y in enumerate(b,1):curr.append(min(curr[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=curr
 return prev[-1]
def overlap(a,b):
 a=Counter(words(a));b=Counter(words(b));return sum((a&b).values())/max(1,sum(a.values()))
def has_terms(text,terms):
 return all(re.search(r'(?<!\w)'+re.escape(norm(t))+r'(?!\w)',norm(text)) is not None for t in terms)
def metrics(ids,relevant,k=None):
 if not relevant:return None
 r=set(relevant);n=k if k is not None else len(ids);seq=ids[:n];hits=[int(x in r) for x in seq];found=set(seq)&r
 precisions=[sum(hits[:i+1])/(i+1) for i,h in enumerate(hits) if h]
 dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits));ideal=sum(1/math.log2(i+2) for i in range(min(n,len(r))))
 return dict(precision=len(found)/max(1,n),recall=len(found)/len(r),hit=float(bool(found)),mrr=next((1/(i+1) for i,h in enumerate(hits) if h),0),ndcg=dcg/ideal if ideal else 0,ap=sum(precisions)/len(r))
def keyfile(kind,key):return CACHE/kind/(digest(key)+'.json')
class CachedEngine:
 def __init__(self):
  self.base=LocalModels(replace(settings,storage=E/'runtime',database_url='postgresql://INVALID_EVALUATION_NEVER_CONNECT'))
  self.cfg=self.base.cfg;self.status=self.base.status;self.text_identity=self.base.text_identity;self.image_identity=self.base.image_identity;self.calls=[];self.rerank_input=[];self.usage=[]
 def call(self,kind,key,fn):
  p=keyfile(kind,[FINGERPRINT,key]);start=time.perf_counter()
  if p.exists(): r=json.loads(p.read_text());cached=True
  else:
   val=fn();r={'value':val,'elapsed':time.perf_counter()-start};cached=False
   if val is not None:save(p,r)
  self.calls.append({'stage':kind,'seconds':r['elapsed'],'cached':cached});return r['value']
 def embed_text(self,texts,query=False):return self.call('text_embedding',[texts,query,self.text_identity],lambda:self.base.embed_text(texts,query=query))
 def embed_image_space(self,*,image=None,text=None):return self.call('image_embedding',[digest(image.read_bytes().hex()) if image else text,self.image_identity],lambda:self.base.embed_image_space(image=image,text=text))
 def rerank(self,q,texts):
  self.rerank_input=list(texts)
  return self.call('reranking',[q,texts],lambda:self.base.rerank(q,texts))
 def generate(self,q,ev,image=None):
  return self.call('generation',[q,ev,image and digest(image.read_bytes().hex()),self.cfg.generation_model],lambda:self.base.generate(q,ev,image=image))
# Observe the original local HTTP response for usage without altering prompt/answer behavior.
import worker.models as model_module
original_urlopen=model_module.urlopen
class Response:
 def __init__(self,data):self.data=data
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read(self):return self.data
def observed_urlopen(*args,**kw):
 with original_urlopen(*args,**kw) as r: data=r.read()
 try:
  content=json.loads(data);ENGINE.usage.append({k:content.get(k) for k in ['prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration']})
 except Exception:pass
 return Response(data)
model_module.urlopen=observed_urlopen
FINGERPRINT=digest([ (APP/p).read_text() for p in ['worker/ingestion.py','worker/models.py','worker/retrieval.py']]+['evaluation-schema-v2',(E/'build_testset.py').read_text()])
ENGINE=CachedEngine()

def ingest(manifests):
 p=CACHE/'corpus.json'
 if p.exists():
  v=json.loads(p.read_text())
  if v['fingerprint']==FINGERPRINT:return v['chunks'],v['parsing']
 corpus=[];stats=[]
 for m in manifests:
  start=time.perf_counter();out=E/'runtime'/m['id'];out.mkdir(parents=True,exist_ok=True)
  chunks=extract(E/m['file'],'application/pdf',out,ENGINE.cfg);extraction=time.perf_counter()-start
  t=time.perf_counter();emb=ENGINE.embed_text([c.text for c in chunks]);vectors={}
  for c in chunks:
   if c.image_path and c.image_path not in vectors:vectors[c.image_path]=ENGINE.embed_image_space(image=Path(c.image_path))
  embed=time.perf_counter()-t
  rows=[]
  for i,c in enumerate(chunks):
   row=asdict(c);row.update(id=f"{m['id']}-p{c.page}-c{i:03}",source_id=m['id'],version_id=m['id']+'-v1',title=m['id']+'.pdf',source_modality=m['id'],embedding=emb[i] if emb else None,embedding_model=ENGINE.text_identity if emb else None,image_embedding=vectors.get(c.image_path),image_embedding_model=ENGINE.image_identity if vectors.get(c.image_path) else None)
   rows.append(row)
  corpus+=rows
  pages=[]
  for pg in m['pages']:
   found='\n'.join(c['text'] for c in rows if c['page']==pg['page']);ref=pg['text'];pages.append(dict(page=pg['page'],text_completeness=overlap(ref,found),cer=edit(norm(ref),norm(found))/max(1,len(norm(ref))) if m['id']=='scanned' else None,wer=edit(words(ref),words(found))/max(1,len(words(ref))) if m['id']=='scanned' else None,reference=ref,extracted=found))
  table=[]
  for gt in m['tables']:
   found='\n'.join(c['text'] for c in rows if c['page']==gt['page']);table.append({'page':gt['page'],'cell_content_accuracy':mean([float(has_terms(found,[cell])) for row in gt['cells'] for cell in row]),'structured_cells_accuracy':0.,'row_column_structure_preservation':0.,'reason':'App emits flat text, no table row/column structure.'})
  stats.append(dict(modality=m['id'],pages=pages,tables=table,figure_detection_recall=0. if m['figures'] else None,figures_expected=len(m['figures']),figures_detected=0,preview_page_coverage=len({c['page'] for c in rows if c['image_path']})/len(m['pages']),page_mapping_accuracy=mean([float(1<=c['page']<=len(m['pages'])) for c in rows]),extraction_seconds=extraction,embedding_seconds=embed,ingestion_seconds_per_page=(time.perf_counter()-start)/len(m['pages']),chunk_count=len(rows),chunk_sizes=[len(c['text']) for c in rows]))
  print('Ingested',m['id'],len(rows),'chunks',flush=True)
 save(p,dict(fingerprint=FINGERPRINT,chunks=corpus,parsing=stats));return corpus,stats

def ground_truth(q,corpus):
 # Relevant pages independently authored. Chunk gold is a deterministic mapping of that page annotation;
 # semantic evidence coverage is reported separately, preventing page-preview hits hiding absent visual text.
 relevant=[c['id'] for c in corpus if c['source_id']==q['modality'] and c['page'] in q['source_pages']]
 return relevant

def ragas_scores(q,result,candidates):
 from judges import score_ragas
 return score_ragas(q,result,candidates,ENGINE,E,FINGERPRINT)

def evaluate(q,corpus):
 p=CACHE/'questions'/(q['id']+'.json')
 if p.exists():
  old=json.loads(p.read_text())
  if old['fingerprint']==FINGERPRINT and old['result'].get('mode')!='extractive':
   # Reattempt only unavailable judge metrics when credentials appear.
   if os.getenv('OPENROUTER_API_KEY') and old.get('ragas',{}).get('judge_status')!='complete':
    cs=[next(c for c in corpus if c['id']==cid) for cid in old['retrieved_ids']];old['ragas']=ragas_scores(q,old['result'],cs);save(p,old)
   return old
 ENGINE.calls=[];ENGINE.usage=[];start=time.perf_counter();candidates=rank_candidates(q['question'],corpus,engine=ENGINE);retrieval=time.perf_counter()-start
 before=[]
 for text in ENGINE.rerank_input:
  match=next((c['id'] for c in corpus if c['text']==text and c['id'] not in before),None)
  if match:before.append(match)
 t=time.perf_counter();result=answer_from_evidence(q['question'],candidates,engine=ENGINE);generation=time.perf_counter()-t
 ids=[c['id'] for c in candidates];relevant=ground_truth(q,corpus);answer=result['answer'];abstain=result['mode']=='abstention'
 citations=result['citations'];lookup={c['id']:c for c in corpus}
 citation_correct=[float(c['id'] in relevant and c['text'] in lookup.get(c['id'],{}).get('text','')) for c in citations]
 grounded=[]
 for c in citations:
  region_ok=False
  if c.get('bbox') and q['source_regions']:
   a=fitz.Rect(c['bbox']);region_ok=any(a.intersects(fitz.Rect(b)) for b in q['source_regions'])
  elif c.get('bbox'):region_ok=True
  grounded.append(float(c['id'] in relevant and region_ok))
 # Deterministic evidence-term coverage is a diagnostic, NOT answer correctness/faithfulness.
 terms=mean([float(has_terms(answer,[term])) for term in q['evidence_terms']]) if not q['unanswerable'] else None
 r=dict(id=q['id'],fingerprint=FINGERPRINT,question=q['question'],modality=q['modality'],type=q['type'],reference_answer=q['reference_answer'],source_pages=q['source_pages'],relevant_ids=relevant,retrieved_ids=ids,before_ids=before,result=result,unanswerable=q['unanswerable'],abstention=abstain,reference_term_coverage=terms,correct_negative=float(abstain) if q['unanswerable'] else None,negative_nonabstention=float(not abstain) if q['unanswerable'] else None,citation_source_accuracy=mean(citation_correct),citation_visual_region_match=mean(grounded),has_valid_citation=float(bool(citations) and all(citation_correct)) if not q['unanswerable'] else None,clickable_app_citation=None,metrics={str(k):metrics(ids,relevant,k) for k in [1,3,5,10]},before_metrics={str(k):metrics(before[:5],relevant,k) for k in [1,3,5,10]},final_metrics=metrics(ids,relevant),topk_modality_mix={str(k):dict(Counter(lookup[i]['source_modality'] for i in ids[:k])) for k in [1,3,5,10]},source_modality_hit=float(any(c['source_modality']==q['modality'] for c in candidates)) if relevant else None,app_modality_mix=dict(Counter(c['modality'] for c in candidates)),evidence_present_in_text=float(has_terms(' '.join(c['text'] for c in corpus if c['id'] in relevant),q['evidence_terms'])) if relevant else None,timings={'retrieval':retrieval,'generation':generation,'total':time.perf_counter()-start},stage_calls=list(ENGINE.calls),token_usage=list(ENGINE.usage),ragas=ragas_scores(q,result,candidates))
 save(p,r);print(q['id'],result['mode'],'recall@5',r['metrics']['5'] and round(r['metrics']['5']['recall'],3),flush=True);return r

def robustness(corpus,questions):
 p=CACHE/'robustness.json'
 if p.exists():
  r=json.loads(p.read_text())
  if r['fingerprint']==FINGERPRINT:return r['results']
 root=E/'runtime/robustness';root.mkdir(parents=True,exist_ok=True);out=[]
 original=fitz.open(E/'fixtures/scanned.pdf');pix=original[0].get_pixmap(matrix=fitz.Matrix(2,2));base=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
 variants={'low_resolution':base.resize((300,375)).resize(base.size),'rotated_90':base.rotate(90,expand=True),'blur_noise':base.filter(ImageFilter.GaussianBlur(3)),'mixed_language':raster(['HomeAtlas evaluation: scanned record 1','Pump S1 was inspected on 2026-01-15.','Pump S1 pressure was 3 bar.','Presion de la bomba: tres bares.','Prochaine inspection: 2027.'])}
 arr=np.asarray(variants['blur_noise']).astype(np.int16);rng=np.random.default_rng(SEED);arr=np.clip(arr+rng.normal(0,22,arr.shape),0,255).astype(np.uint8);variants['blur_noise']=Image.fromarray(arr)
 reference='HomeAtlas evaluation: scanned record 1 Pump S1 was inspected on 2026-01-15. Pump S1 pressure was 3 bar. Technician: Morgan 1. Next inspection: 2027.'
 for name,im in variants.items():
  pdf=fitz.open();page=pdf.new_page(width=600,height=750);page.insert_image(page.rect,stream=png(im));path=root/(name+'.pdf');pdf.save(path);pdf.close();chunks=extract(path,'application/pdf',root/name,ENGINE.cfg)
  text=' '.join(c.text for c in chunks);ref=reference if name!='mixed_language' else 'HomeAtlas evaluation: scanned record 1 Pump S1 was inspected on 2026-01-15. Pump S1 pressure was 3 bar. Presion de la bomba: tres bares. Prochaine inspection: 2027.'
  emb=ENGINE.embed_text([c.text for c in chunks]);rows=[];image_vectors={}
  for c in chunks:
   if c.image_path and c.image_path not in image_vectors:image_vectors[c.image_path]=ENGINE.embed_image_space(image=Path(c.image_path))
  for i,c in enumerate(chunks):
   row=asdict(c);row.update(id=f'robust-{name}-{i}',source_id='scanned',version_id='robust-v1',title=name,source_modality='scanned',embedding=emb[i] if emb else None,embedding_model=ENGINE.text_identity if emb else None,image_embedding=image_vectors.get(c.image_path),image_embedding_model=ENGINE.image_identity if image_vectors.get(c.image_path) else None);rows.append(row)
  # Same two baseline questions, replace only the first scan page in full corpus.
  docs=[c for c in corpus if not(c['source_id']=='scanned' and c['page']==1)]+rows
  runs=[]
  for q in [x for x in questions if x['id'] in ['scanned-01','scanned-02']]:
   cs=rank_candidates(q['question'],docs,engine=ENGINE);a=answer_from_evidence(q['question'],cs,engine=ENGINE);baseline=json.loads((CACHE/'questions'/(q['id']+'.json')).read_text()) if (CACHE/'questions'/(q['id']+'.json')).exists() else None
   cov=mean([float(has_terms(a['answer'],[t])) for t in q['evidence_terms']]);runs.append({'id':q['id'],'answer':a,'term_coverage':cov,'baseline_term_coverage':baseline and baseline['reference_term_coverage'],'score_drop':baseline['reference_term_coverage']-cov if baseline else None})
  out.append({'variant':name,'cer':edit(norm(ref),norm(text))/len(norm(ref)),'wer':edit(words(ref),words(text))/len(words(ref)),'reference':ref,'extracted':text,'questions':runs})
 save(p,dict(fingerprint=FINGERPRINT,results=out));return out

def image_queries(corpus):
 p=CACHE/'image_queries.json'
 if p.exists():
  r=json.loads(p.read_text())
  if r['fingerprint']==FINGERPRINT:return r['results']
 rows=[]
 for mod in ['text','table','image','chart','scanned']:
  im=Path(next(c['image_path'] for c in corpus if c['source_id']==mod and c['page']==1));ocr=' '.join(c.text for c in ocr_image(Image.open(im),ENGINE.cfg));q='Find the record shown in this photo.'
  cs=rank_candidates(q+' '+ocr[:1500],corpus,engine=ENGINE,image=im)
  rows.append({'modality':mod,'query_image':str(im.relative_to(E)),'source_page_hit_at_5':float(any(c['source_id']==mod and c['page']==1 for c in cs)),'image_query_to_text_hit_at_5':float(any(c['source_id']==mod and c['page']==1 and c['modality']=='text' for c in cs)),'retrieved_ids':[c['id'] for c in cs],'app_modality_mix':dict(Counter(c['modality'] for c in cs))})
 save(p,dict(fingerprint=FINGERPRINT,results=rows));return rows

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--modality',choices=['text','table','image','chart','scanned']);args=parser.parse_args()
 # Private judge env only; never display values. App config had already loaded its local env.
 from dotenv import load_dotenv
 load_dotenv(E/'.env',override=False)
 if not (E/'testset.json').exists():build()
 testset=json.loads((E/'testset.json').read_text());questions=testset['questions'];manifests=json.loads((E/'fixtures/manifest.json').read_text())
 corpus,parsing=ingest(manifests)
 # Independently authored page text validates mapping, not merely page-number bounds.
 refs={(m['id'],pg['page']):norm(pg['text']) for m in manifests for pg in m['pages']}
 for stat in parsing:
  rows=[c for c in corpus if c['source_id']==stat['modality']]
  stat['page_bounds_accuracy']=stat['page_mapping_accuracy']
  stat['page_mapping_accuracy']=mean([float(norm(c['text']) in refs.get((c['source_id'],c['page']),'')) for c in rows])
  stat['page_mapping_method']='Normalized exact chunk text must occur in the independently authored source-page transcript; repeated identical lines can be ambiguous.'
 for q in questions:q['reference_chunks']=ground_truth(q,corpus)
 save(E/'testset.json',testset)
 selected=[q for q in questions if not args.modality or q['modality']==args.modality]
 for q in selected:evaluate(q,corpus)
 rows=[]
 for q in questions:
  p=CACHE/'questions'/(q['id']+'.json')
  if p.exists():
   r=json.loads(p.read_text())
   if r['fingerprint']==FINGERPRINT:rows.append(r)
 robust=robustness(corpus,questions) if not args.modality or args.modality=='scanned' else (json.loads((CACHE/'robustness.json').read_text())['results'] if (CACHE/'robustness.json').exists() and json.loads((CACHE/'robustness.json').read_text())['fingerprint']==FINGERPRINT else [])
 imgs=image_queries(corpus)
 from report import write_report
 payload=dict(schema_version=1,seed=SEED,fingerprint=FINGERPRINT,scope='Actual app extract/rank_candidates/answer_from_evidence; in-memory evaluation corpus, no DB/HTTP upload/UI path.',questions=rows,parsing=parsing,robustness=robust,image_queries=imgs,models={'text':ENGINE.text_identity,'image':ENGINE.image_identity,'reranker':ENGINE.cfg.reranker_model+'@'+ENGINE.cfg.reranker_revision,'generation':ENGINE.cfg.generation_model},model_status=ENGINE.status)
 save(E/'results.json',payload)
 with (E/'results.csv').open('w',newline='') as f:
  fields=['id','modality','type','question','reference_answer','answer','mode','recall_at_5','reference_term_coverage','answer_similarity','faithfulness','correct_negative','citation_source_accuracy','latency_seconds'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:v for k,v in dict(id=r['id'],modality=r['modality'],type=r['type'],question=r['question'],reference_answer=r['reference_answer'],answer=r['result']['answer'],mode=r['result']['mode'],recall_at_5=r['metrics']['5']['recall'] if r['metrics']['5'] else None,reference_term_coverage=r['reference_term_coverage'],answer_similarity=r['ragas'].get('answer_similarity'),faithfulness=r['ragas'].get('faithfulness'),correct_negative=r['correct_negative'],citation_source_accuracy=r['citation_source_accuracy'],latency_seconds=r['timings']['total']).items()})
 write_report(payload,E)
if __name__=='__main__':main()
