"""Actual RAGAS 0.2.15 metrics; free-tier-only judge, persistent per-request cache."""
import os,json,time,hashlib,asyncio,math,email.utils,datetime
from pathlib import Path
import httpx
from ragas import SingleTurnSample
from ragas.run_config import RunConfig
from ragas.embeddings import BaseRagasEmbeddings
from ragas.llms import BaseRagasLLM
from ragas.metrics import (AnswerSimilarity,Faithfulness,AnswerRelevancy,LLMContextPrecisionWithReference,LLMContextRecall,AnswerCorrectness,MultiModalFaithfulness,MultiModalRelevance)
from langchain_core.outputs import LLMResult,Generation
METRICS=['faithfulness','answer_relevancy','context_precision','context_recall','answer_correctness','multimodal_faithfulness','multimodal_relevance']
class AppEmbeddings(BaseRagasEmbeddings):
 def __init__(self,engine):super().__init__();self.engine=engine;self.set_run_config(RunConfig(max_retries=1))
 def embed_documents(self,texts):
  v=self.engine.embed_text(texts)
  if v is None:raise RuntimeError('App text embeddings unavailable')
  return v
 def embed_query(self,text):return self.embed_documents([text])[0]
 async def aembed_documents(self,texts):return self.embed_documents(texts)
 async def aembed_query(self,text):return self.embed_query(text)
class FreeJudge(BaseRagasLLM):
 def __init__(self,root):super().__init__(run_config=RunConfig(max_retries=1,timeout=180));self.root=root;self.model=os.getenv('EVAL_JUDGE_MODEL','openrouter/free')
 def request(self,messages):
  if not(self.model.endswith(':free') or self.model=='openrouter/free'):raise ValueError('Only free-tier model IDs are allowed')
  payload={'model':self.model,'messages':messages,'temperature':0,'seed':741,'max_tokens':2500}
  key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();p=self.root/'cache/judge'/(key+'.json');p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():return json.loads(p.read_text())
  token=os.getenv('OPENROUTER_API_KEY')
  if not token:raise RuntimeError('OPENROUTER_API_KEY missing')
  last=None
  for attempt in range(5):
   try:
    response=httpx.post('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},json=payload,timeout=120)
    if response.status_code in [429,500,502,503,504]:
     retry=response.headers.get('retry-after','');delay=min(60,2**attempt+0.25)
     try:delay=max(delay,min(60,float(retry)))
     except ValueError:pass
     last=RuntimeError('Free judge HTTP '+str(response.status_code));time.sleep(delay);continue
    if response.status_code!=200:raise RuntimeError('Free judge HTTP '+str(response.status_code))
    data=response.json()
    if 'choices' not in data:raise RuntimeError('Free judge did not return choices')
    p.write_text(json.dumps(data));return data
   except (httpx.TimeoutException,httpx.NetworkError) as exc:last=RuntimeError(type(exc).__name__);time.sleep(min(60,2**attempt))
  raise last or RuntimeError('Free judge retry budget exhausted')
 def generate_text(self,prompt,n=1,temperature=0,stop=None,callbacks=None):
  messages=[{'role':'assistant' if m.type=='ai' else 'system' if m.type=='system' else 'user','content':m.content} for m in prompt.to_messages()]
  outputs=[]
  for _ in range(n):
   result=self.request(messages);outputs.append(Generation(text=result['choices'][0]['message']['content']))
  return LLMResult(generations=[outputs])
 async def agenerate_text(self,prompt,n=1,temperature=None,stop=None,callbacks=None):return await asyncio.to_thread(self.generate_text,prompt,n,temperature,stop,callbacks)
 def is_finished(self,response):return True

def score_ragas(q,result,candidates,engine,root,fingerprint):
 embeddings=AppEmbeddings(engine);sample=SingleTurnSample(user_input=q['question'],response=result['answer'],reference=q['reference_answer'],retrieved_contexts=[c['text'] for c in candidates])
 scores={k:None for k in METRICS};scores.update(answer_similarity=None,judge_status='unavailable',errors={})
 try:scores['answer_similarity']=asyncio.run(AnswerSimilarity(embeddings=embeddings).single_turn_ascore(sample))
 except Exception as exc:scores['errors']['answer_similarity']=type(exc).__name__+': '+str(exc)[:160]
 if not os.getenv('OPENROUTER_API_KEY'):
  scores['reason']='No free-tier judge credential configured (OPENROUTER_API_KEY).';return scores
 judge=FreeJudge(root)
 metrics={'faithfulness':Faithfulness(llm=judge),'answer_relevancy':AnswerRelevancy(llm=judge,embeddings=embeddings),'context_precision':LLMContextPrecisionWithReference(llm=judge),'context_recall':LLMContextRecall(llm=judge),'answer_correctness':AnswerCorrectness(llm=judge,embeddings=embeddings),'multimodal_faithfulness':MultiModalFaithfulness(llm=judge),'multimodal_relevance':MultiModalRelevance(llm=judge)}
 for name,metric in metrics.items():
  target=sample
  if name.startswith('multimodal'):
   contexts=[c['text'] for c in candidates]+list(dict.fromkeys(c['image_path'] for c in candidates if c.get('image_path')))
   target=SingleTurnSample(user_input=q['question'],response=result['answer'],reference=q['reference_answer'],retrieved_contexts=contexts)
  # Metric-level result cache prevents successful metrics being rerun after another fails.
  key=hashlib.sha256(json.dumps([fingerprint,name,judge.model,target.to_dict()],sort_keys=True).encode()).hexdigest();p=root/'cache/judge_metrics'/(key+'.json');p.parent.mkdir(parents=True,exist_ok=True)
  try:
   if p.exists():value=json.loads(p.read_text())['value']
   else:
    value=asyncio.run(metric.single_turn_ascore(target));value=value if math.isfinite(value) else None
    if value is not None:p.write_text(json.dumps({'value':value}))
   scores[name]=value
  except Exception as exc:scores['errors'][name]=type(exc).__name__ # Do not leak credential-bearing HTTP exception strings.
 scores['judge_status']='complete' if all(scores[k] is not None for k in METRICS) else 'partial'
 scores['judge_model']=judge.model
 return scores
