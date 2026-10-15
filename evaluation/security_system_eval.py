#!/usr/bin/env python3
"""Group J/K: disposable live security probes and measured system performance."""
from __future__ import annotations
import json,os,sys,subprocess,time,tempfile,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'evaluation'
sys.path[:0]=[str(ROOT),str(E)]
from protocol import argument_parser,frozen_dataset,make_result,write_result,metric,shared_generation_slot,digest,app_fingerprint
MAIN=Path(os.environ.get('EVAL_APP_ROOT',str(ROOT if (ROOT/'.env.local').exists() else ROOT.parents[1]/'homeatlas')))
RUNTIME=E/'runtime'/'security-system'
EXPECTED_PROBES=['isolation-own-answer-A','cache-own-exact-hit-A','cache-cross-household-no-replay','cache-same-household-user-isolation','cache-second-user-own-hit','cross-household-/api/atlas','cross-household-/api/cache','cross-household-/api/export','cross-household-query-denied','cross-household-item-id-denied','editor-cache-admin-denied','anonymous-household-denied','cache-stored-content-policy','latency-sequential-0','latency-sequential-1',*[f'latency-concurrent-{i}' for i in range(4)],'source-injection-classic-ingestion','source-injection-classic','source-injection-classic-cross-household-preview','query-injection','source-injection-indirect-ingestion','source-injection-indirect','source-injection-indirect-cross-household-preview','health']

def quantile(values,p):
 values=sorted(values)
 if not values:return None
 x=(len(values)-1)*p;lo=int(x);hi=min(lo+1,len(values)-1)
 return values[lo]*(hi-x)+values[hi]*(x-lo) if hi!=lo else values[lo]

def secret_scan():
 from dotenv import dotenv_values
 values=dotenv_values(MAIN/'.env.local')
 secrets={k:v for k,v in values.items() if v and len(v)>=16 and re.search('KEY|SECRET|PASSWORD|DATABASE_URL',k)}
 roots=[MAIN/'evaluation',*list((MAIN.parent/'.eval-worktrees').glob('*/evaluation'))]
 found=[];count=0;danger=[]
 for root in roots:
  paths=[*root.glob('*.py'),*root.glob('*.mjs'),*root.glob('results/*.json')]
  for p in paths:
   if not p.is_file():continue
   text=p.read_text(errors='replace');count+=1
   # Never store matching secret values, only names and repository-relative paths.
   names=[name for name,value in secrets.items() if value in text]
   if names:found.append({'agent_directory':root.parent.name,'file':str(p.relative_to(root)),'sensitive_key_names':names})
   if re.search(r'asdict\(\s*(?:cfg|settings)\s*\)|(?:vars|__dict__)\(\s*settings',text):danger.append({'agent_directory':root.parent.name,'file':str(p.relative_to(root))})
 return {'id':'publication-sensitive-value-scan','files_scanned':count,'matching_files':found,'unsafe_settings_dump_patterns':danger,'passed':not found,'scope':'Evaluator source and published results only. No actual user logs or uploads read.'}

def parser_scaling():
 from dotenv import load_dotenv
 load_dotenv(MAIN/'.env.local',override=False)
 from worker.ingestion import extract
 rows=[]
 with tempfile.TemporaryDirectory(prefix='homeatlas-synthetic-scaling-') as td:
  root=Path(td)
  for size in [4096,262144,2097152]:
   line='Synthetic appliance service reminder, warranty date 2027-07-19, Study desk drawer.\n'
   text=(line*(size//len(line)+1))[:size];p=root/f'{size}.txt';p.write_text(text)
   start=time.perf_counter();err=None;chunks=[]
   try:chunks=extract(p,'text/plain',root/f'artifacts-{size}')
   except Exception as e:err=type(e).__name__
   rows.append({'id':f'scaling-text-{size}','bytes':size,'seconds':time.perf_counter()-start,'chunks':len(chunks),'error':err,'scope':'Text validation and extraction only; excludes upload, embeddings and database publication.'})
 return rows

def generation_observations(phase,run):
 override=os.environ.get('EVAL_GENERATION_RESULTS')
 candidates=[Path(override)] if override else [ROOT.parent/'generation/evaluation/results/generation-agent.json',MAIN/'evaluation/results/generation-agent.json']
 source=next((p for p in candidates if p.exists()),None)
 if not source:return [],{'generation_results':'not yet available'}
 data=json.loads(source.read_text());r=next((r for r in data['runs'] if r['phase']==phase and r['run']==run),None)
 if not r:return [],{'generation_results':'requested phase/run not yet available'}
 rows=[]
 for q in r['per_question']:
  calls=q.get('stage_calls',[]);usage=[u for c in calls for u in c.get('usage',[]) if isinstance(u,dict)]
  rows.append({'id':q['id'],'run_id':r['run_id'],'suite':q['suite'],'modality':q['modality'],'timings':q.get('timings',{}),'stage_calls':calls,'prompt_tokens':sum(u.get('prompt_eval_count') or 0 for u in usage),'completion_tokens':sum(u.get('eval_count') or 0 for u in usage),'usage_calls':len(usage),'model_calls':sum(c.get('stage') in ('generation','verification') for c in calls),'actual_new_model_calls':sum(c.get('stage') in ('generation','verification') and not c.get('cached') for c in calls),'evaluation_response_replayed':any(c.get('cached') for c in calls),'abstained':q.get('result',{}).get('mode')=='abstention','failure':any(u.get('error') for u in usage),'observed_model_ids':sorted({u['served_model'] for u in usage if u.get('served_model')})})
 return rows,{'generation_result_hash':digest(r),'generation_rows':len(rows),'generation_partial':r.get('config',{}).get('partial',len(rows)<60),'generation_app_source_fingerprint':r['app_source_fingerprint'],'generation_observed_models':r.get('config',{}).get('observed_models',{})}

def summarize(live,scaling,generation):
 ms=[]
 def group(name,rows):
  ms.append(metric(name,sum(bool(r['passed']) for r in rows)/len(rows) if rows else None,len(rows),reason=None if rows else 'No completed live observations'))
 security=[r for r in live if r['id'].startswith(('isolation-','cache-cross','cache-same','cross-household','anonymous-','editor-'))]
 group('security_isolation_pass_rate',security)
 attacks=[r for r in live if r['id'] in ['source-injection-classic','source-injection-indirect','query-injection']]
 eligible=[r for r in attacks if r.get('full_model_pipeline')]
 ms.append(metric('prompt_injection_resistance_rate',sum(r['passed'] for r in eligible)/len(eligible) if eligible else None,len(eligible),reason=None if eligible else 'No attack query completed with a local model grounded/explained response; transport/abstention cannot establish generative injection resistance.'))
 group('prompt_injection_http_safety_rate',attacks)
 ms.append(metric('prompt_injection_answer_fact_rate',sum(r['expected_fact_present'] for r in attacks)/len(attacks) if attacks else None,len(attacks),reason=None if attacks else 'No completed attack queries'))
 for concurrency,label in [(1,'sequential'),(4,'concurrent')]:
  rows=[r for r in live if r.get('concurrency')==concurrency];values=[r['latency_ms'] for r in rows]
  for p in [.5,.95]:ms.append(metric(f'live_recorded_fact_{label}_p{int(p*100)}_ms',quantile(values,p),len(values),reason=None if values else 'No successful timing probes'))
  ms.append(metric(f'live_recorded_fact_{label}_failure_rate',sum(r['status']!=200 for r in rows)/len(rows) if rows else None,len(rows),reason=None if rows else 'No probes'))
 batch=[r for r in live if r.get('concurrency')==4]
 ms.append(metric('live_recorded_fact_concurrent_throughput_rps',len(batch)/(batch[0]['batch_wall_ms']/1000) if batch else None,len(batch),reason=None if batch else 'No concurrent batch'))
 for row in scaling:ms.append(metric(f"parse_text_{row['bytes']}_bytes_seconds",row['seconds'],1,bytes=row['bytes'],chunks=row['chunks'],error=row['error']))
 for modality in ['all','text','table','image','chart','scanned']:
  rows=[r for r in generation if modality=='all' or r['modality']==modality]
  for stage in ['retrieval_seconds','generation_seconds','total_seconds']:
   vals=[r['timings'][stage] for r in rows if stage in r['timings']]
   for p in [.5,.95]:ms.append(metric(f'pdf_{modality}_{stage}_p{int(p*100)}',quantile(vals,p),len(vals),reason=None if vals else 'Generation-agent observations for this phase/run/modality not available yet'))
  for stage in ['embedding','reranking','generation','verification']:
   vals=[c['seconds'] for r in rows for c in r['stage_calls'] if c['stage']==stage]
   for p in [.5,.95]:ms.append(metric(f'pdf_{modality}_model_{stage}_seconds_p{int(p*100)}',quantile(vals,p),len(vals),reason=None if vals else 'No recorded timed model calls observed'))
  for token in ['prompt_tokens','completion_tokens','model_calls','actual_new_model_calls']:
   vals=[r[token] for r in rows if token in ('model_calls','actual_new_model_calls') or r['usage_calls']>0]
   ms.append(metric(f'pdf_{modality}_mean_{token}',statistics.mean(vals) if vals else None,len(vals),reason=None if vals else 'No tokenizer-reported usage captured'))
 for name,reason in [('shared_log_sensitive_canary_leak_rate','Actual process logs may contain private user activity and were deliberately not read. Source logsites inspected separately; that is not a measured log-leak test.'),('three_d_active_render_fps','No renderer instrumentation or isolated authenticated disposable GPU browser measurement in this runner. Display requestAnimationFrame rate is not scene rendering FPS.'),('three_d_view_ready_seconds','No isolated disposable browser navigation measurement executed.'),('cost_usd_per_query','Self-hosted model has no per-token invoice. Electricity/hardware amortization and deployment prices were not instrumented; zero API billing is not zero total cost.'),('full_rag_concurrency_capacity','Concurrent sample measures saved inventory field lookup only. Shared model lock serializes actual generation to protect this 16 GB development host; cannot infer production generation concurrency.'),('pdf_timeout_rate','Generation raw stage rows do not distinguish timeout, parse failure and abstention. No invented classification.')]:ms.append(metric(name,None,0,reason=reason))
 return ms

def statistic_samples(live,generation):
 """Expose raw numeric units and exact aggregation for independent bootstrap CIs."""
 out={}
 def add(name,rows,value,aggregation='mean',p=None):
  samples=[{'id':str(r['id']), 'value':float(value(r))} for r in rows]
  if samples:out[name]={'aggregation':aggregation,'quantile':p,'samples':samples}
 security=[r for r in live if r['id'].startswith(('isolation-','cache-cross','cache-same','cross-household','anonymous-','editor-'))]
 add('security_isolation_pass_rate',security,lambda r:r['passed'])
 attacks=[r for r in live if r['id'] in ['source-injection-classic','source-injection-indirect','query-injection']]
 add('prompt_injection_resistance_rate',[r for r in attacks if r.get('full_model_pipeline')],lambda r:r['passed'])
 add('prompt_injection_http_safety_rate',attacks,lambda r:r['passed'])
 add('prompt_injection_answer_fact_rate',attacks,lambda r:r['expected_fact_present'])
 for concurrency,label in [(1,'sequential'),(4,'concurrent')]:
  rows=[r for r in live if r.get('concurrency')==concurrency]
  for p in [.5,.95]:add(f'live_recorded_fact_{label}_p{int(p*100)}_ms',rows,lambda r:r['latency_ms'],'quantile',p)
  add(f'live_recorded_fact_{label}_failure_rate',rows,lambda r:r['status']!=200)
 for modality in ['all','text','table','image','chart','scanned']:
  rows=[r for r in generation if modality=='all' or r['modality']==modality]
  for stage in ['retrieval_seconds','generation_seconds','total_seconds']:
   for p in [.5,.95]:add(f'pdf_{modality}_{stage}_p{int(p*100)}',[r for r in rows if stage in r['timings']],lambda r:r['timings'][stage],'quantile',p)
  for stage in ['embedding','reranking','generation','verification']:
   calls=[dict(c,id=r['id']+'/'+stage+'/'+str(i)) for r in rows for i,c in enumerate(r['stage_calls']) if c['stage']==stage]
   for p in [.5,.95]:add(f'pdf_{modality}_model_{stage}_seconds_p{int(p*100)}',calls,lambda c:c['seconds'],'quantile',p)
  for token in ['prompt_tokens','completion_tokens','model_calls','actual_new_model_calls']:
   add(f'pdf_{modality}_mean_{token}',[r for r in rows if token in ('model_calls','actual_new_model_calls') or r['usage_calls']>0],lambda r:r[token])
 return out

def main():
 p=argument_parser(__doc__);p.add_argument('--refresh-performance-only',action='store_true');args=p.parse_args();frozen_dataset();RUNTIME.mkdir(parents=True,exist_ok=True)
 raw=RUNTIME/f'{args.phase}-{args.run}.json';scalepath=RUNTIME/f'{args.phase}-{args.run}-scaling.json'
 if not args.refresh_performance_only:
  env={**os.environ,'EVAL_APP_ROOT':str(MAIN),'EVAL_RAW_OUTPUT':str(raw),'EVAL_RUN_ID':f'{args.phase}-run-{args.run:02}'}
  before=time.perf_counter()
  with shared_generation_slot():
   gate_wait=time.perf_counter()-before
   done=subprocess.run(['node','--env-file='+str(MAIN/'.env.local'),str(E/'security_system_live.mjs')],env=env,cwd=MAIN,capture_output=True,text=True,timeout=1500)
  if done.returncode:raise RuntimeError('Disposable HTTP evaluator failed; '+done.stderr[-400:].replace(str(MAIN),'APP_ROOT'))
  print(done.stdout.strip(),flush=True)
  scaling=parser_scaling();scalepath.write_text(json.dumps({'rows':scaling,'gate_wait_seconds':gate_wait}))
 if not raw.exists():raise RuntimeError('No previous actual HTTP observations to refresh')
 live=json.loads(raw.read_text())['rows'];live_fingerprint=app_fingerprint(MAIN)['app_source_fingerprint'];runner_fingerprint=app_fingerprint()['app_source_fingerprint'];scalefile=json.loads(scalepath.read_text());scaling=scalefile['rows'];generation,observed=generation_observations(args.phase,args.run);scan=secret_scan()
 rows=[{**r,'run_id':f'{args.phase}-run-{args.run:02}','group':'J/K-live'} for r in live]+[{**r,'run_id':f'{args.phase}-run-{args.run:02}','group':'K-parser-scaling'} for r in scaling]+[{**r,'group':'K-generation-reused'} for r in generation]+[{**scan,'run_id':f'{args.phase}-run-{args.run:02}','group':'J-publication'}]
 metrics=summarize(live,scaling,generation)+[metric('publication_sensitive_value_leak_files',len(scan['matching_files']),scan['files_scanned'])]
 result=make_result('security-system-agent',args.phase,args.run,metrics,rows,{'scope':'Synthetic disposable HTTP auth/accounts/households/cache/source upload; no real customer data read. Two actual source injection probes and one adversarial query per run. Security challenge strings are supplemental tests, frozen canonical datasets remain unchanged.','live_app_source_fingerprint':live_fingerprint,'live_matches_runner_source':live_fingerprint==runner_fingerprint,'live_app_url':'http://localhost:3000','live_worker_url':'http://localhost:8001','model_generation_gate_wait_seconds':scalefile['gate_wait_seconds'],'timing_note':'Live request latency excludes outer gate acquisition wait. PDF total/retrieval/generation wall times are observed evaluator wall, including shared-lock wait and any same-run resume response replay; they are not isolated cold or warm production latency. Model-stage seconds and token usage retain original actual call observations even when a same-run evaluator resume reuses that response. Historical model_calls count original generation/verification attempts; actual_new_model_calls counts nonreplayed attempts during the saved execution. Evaluator response replay is distinct from application semantic caching. Shared 16 GB development host; small samples; no capacity or SLA claim.','quantile_definition':'Linear interpolation, numpy-compatible method=linear. Small n retained beside each metric.','sensitive_cache_policy':'Cache intentionally stores authorized query text, answer JSON and citations; scoped per household AND user. Synthetic canary confirms this persistence, so zero-PII-in-cache is not asserted. Cache is not a general secrets vault.','request_timeout_seconds':300,'live_probe_count':len(live),'expected_live_probe_count':len(EXPECTED_PROBES),'expected_live_probe_ids':EXPECTED_PROBES,'missing_live_probe_ids':sorted(set(EXPECTED_PROBES)-{r['id'] for r in live}),'complete':live_fingerprint==runner_fingerprint and set(EXPECTED_PROBES)=={r['id'] for r in live} and len(live)==len(EXPECTED_PROBES) and len(generation)==60 and not observed.get('generation_partial',True),'requested_pdf_questions':60,**observed})
 result['statistic_samples']=statistic_samples(live,generation)
 write_result(args.output,result);print(json.dumps({'run_id':result['run_id'],'metrics':len(metrics),'live_probes':len(live),'pdf_observations':len(generation),'failed_probe_ids':[r['id'] for r in live if not r['passed']],'publication_leak_files':len(scan['matching_files'])}),flush=True)
if __name__=='__main__':main()
