#!/usr/bin/env python3
"""Summarize existing specialist observations after the explicit user budget stop.

Read-only with respect to application, gold, raw observations and frozen baseline.
No benchmark, model inference or canonical final snapshot is executed here.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

E = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(E))
from protocol import app_fingerprint, frozen_dataset
from stats_analysis import AGENTS, INFERENCE_AGENTS, aggregate_metrics, digest, paired_significance
from requested_coverage import augment, coverage_markdown
from independent_review import collect as collect_review, write as write_review, bind as bind_review, markdown as review_markdown

SELECTED = {
 'retrieval-agent': ['all/hybrid_runtime/precision@5','all/hybrid_runtime/recall@5',
   'all/hybrid_runtime/mrr@5','all/hybrid_runtime/ndcg@5','all/hybrid_runtime/hit@5',
   'typo/hybrid_runtime/mrr@5','typo/fuzzy/mrr@5'],
 'ingestion-agent': ['ocr.scanned.cer_macro','ocr.scanned.wer_macro','table.cell_text_recall',
   'table.structured_output_rate','chart.numeric_label_text_recall'],
 'homeatlas-agent': ['E.full_path_accuracy','E.container_accuracy',
   'E.document_identifier_fact_presence','E.document_date_fact_presence','E.document_amount_fact_presence',
   'E.aggregate_fact_presence','H.exact_hit_rate','H.variant_hit_rate','H.variant_answer_accuracy',
   'H.variant_correct_answer_hit_rate','H.near_miss_false_hit_rate','H.move_delete_invalidation'],
 'security-system-agent': ['sensitive_answer_cache_persistence_rate'],
 'generation-agent': ['citation_gold_precision','citation_gold_recall','citation_gold_f1',
   'citation_gold_page_recall','citation_exact_quote_rate','false_refusal_rate','abstention_recall',
   'token_f1','rouge_l'],
}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def num(value): return 'NOT MEASURED' if value is None else f'{value:.6g}'
def esc(value): return str(value).replace('|','\\|').replace('\n',' ')
def save(path,payload): path.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--app-root',type=Path,default=E.parent)
 p.add_argument('--output-dir',type=Path,default=E)
 args=p.parse_args(); app=args.app_root.resolve(); out=args.output_dir.resolve()
 out.mkdir(parents=True,exist_ok=True)
 baseline_path=app/'evaluation/baseline_results.json'; baseline_sha=sha(baseline_path)
 baseline=json.loads(baseline_path.read_text()); dataset=frozen_dataset()['dataset_fingerprint']
 fingerprint=app_fingerprint(app)['app_source_fingerprint']
 assert dataset==baseline['dataset_fingerprint'], 'Frozen dataset changed'
 # New showcase helper lives below this directory; original measurement files
 # remain byte-for-byte pinned, including the original full-suite dispatcher.
 for name,expected in baseline['measurement_code']['files'].items():
  assert sha(app/'evaluation'/name)==expected, 'Original measurement file changed: '+name
 sources={}; runs={}; provenance=[]
 for agent in INFERENCE_AGENTS:
  path=app/'evaluation/results'/(agent+'.json'); data=json.loads(path.read_text())
  final=[r for r in data['runs']if r['phase']=='final']; runs[agent]=final
  wanted=[1]if agent=='generation-agent'else[1,2]
  assert sorted(r['run']for r in final)==wanted, 'Unexpected active final run coverage: '+agent
  for r in final:
   assert r['app_source_fingerprint']==fingerprint and r['dataset_fingerprint']==dataset
   assert len({q['id']for q in r['per_question']})==len(r['per_question'])
   if agent in {'homeatlas-agent','ingestion-agent'}: assert r['config'].get('complete')is True
  if agent=='retrieval-agent': assert all(len(r['per_question'])==138 for r in final)
  if agent=='security-system-agent':
   for r in final:
    live=[q for q in r['per_question']if q.get('group')=='J/K-live']
    assert len(live)==27 and {q['id']for q in live}==set(r['config']['expected_live_probe_ids'])
  # Filter only the displayed, original metrics. No full 6,411-row bootstrap.
  chosen=[]
  for r in final:
   values={m['metric']:m for m in r['metrics']}
   assert set(SELECTED[agent])<=set(values)
   chosen.append({**r,'metrics':[values[name]for name in SELECTED[agent]]})
  sources[agent]={'payload':{'runs':chosen}}
  provenance.append({'agent':agent,'file':'results/'+agent+'.json','file_sha256_at_assembly':sha(path),
    'source_runs':[{'phase':r['phase'],'run':r['run'],'run_id':r['run_id'],'app_commit':r['app_commit'],
      'timestamp_utc':r['timestamp_utc'],'complete':r['config'].get('complete'),
      'partial':r['config'].get('partial'),'result_digest_at_assembly':digest(r)}for r in final]})
 gen_data=json.loads((app/'evaluation/results/generation-agent.json').read_text())
 stop=gen_data['partial_final_evidence']; gen=runs['generation-agent'][0]; rows=gen['per_question']
 assert stop['status']=='BUDGET_STOPPED_PARTIAL_FINAL' and gen['config']['partial']is True
 assert stop['scope_change']['saved_main_questions']==len(rows)
 coverage={'saved_questions':len(rows),'planned_questions_per_run':gen['config']['requested_n'],
   'answerable':sum(not r['unanswerable']for r in rows),'negative':sum(r['unanswerable']for r in rows),
   'by_modality':dict(Counter(r['modality']for r in rows)),'last_saved_question':rows[-1]['id'],
   'full_final_runs_completed':0,'second_run_saved_questions':0,'third_pass_saved_questions':0,
   'sampling':'Deterministic stopped prefix, not a random sample. No scanned-PDF generation questions.',
   'scope_change':stop['scope_change']}
 metrics=aggregate_metrics(sources,'final',draws=5000)
 base={(m['agent'],m['metric']):m for m in baseline['metrics']}
 for m in metrics:
  agent=m['agent'];m['phase']='final'
  m['scope']='single stopped prefix'if agent=='generation-agent'else'paired component runs'
  if agent=='security-system-agent':m['scope']='paired live security probes; overall performance group remains incomplete'
  m['source_refs']=[{'file':'results/'+agent+'.json','phase':'final','run':r['run'],'metric_id':m['metric'],
     'value':next(v['value']for v in r['metrics']if v['metric']==m['metric']),
     'n':next(v['n']for v in r['metrics']if v['metric']==m['metric'])}for r in runs[agent]]
  m['baseline']=None if agent=='generation-agent'else base.get((agent,m['metric']))
  if agent=='generation-agent':m['baseline_comparison']='NOT COMPARABLE: stopped prefix versus full baseline; no matched-subset comparison computed.'
 # Timing is descriptive telemetry from these saved question rows, not a model
 # invocation benchmark and not an HTTP timeout rate.
 import numpy as np
 elapsed=[r['timings']['total_seconds']for r in rows]
 telemetry={'saved_query_total_seconds_p50':float(np.quantile(elapsed,.5,method='linear')),
   'saved_query_total_seconds_p95':float(np.quantile(elapsed,.95,method='linear')),'n':len(elapsed),
   'scope':'Observed in-process total query wall time on a shared development host; includes resource waits and same-run resumability effects. Not HTTP end-to-end latency or a production SLA.',
   'logged_timeout_evidence':stop.get('timeout_evidence'),
   'http_timeout_rate':{'value':None,'status':'NOT MEASURED','reason':'Completed-response usage and saved question rows do not enumerate every attempted HTTP request. Logged timeout evidence is reported separately.'},
   'wrapper_counter_note':'generation_model_calls and verification_model_calls count wrapper invocations, not actual HTTP requests. Numeric guards may return before HTTP; usage proves completed responses only.'}
 security=[]
 for r in runs['security-system-agent']:
  live=[q for q in r['per_question']if q.get('group')=='J/K-live']; failed=[q['id']for q in live if not q['passed']]
  security.append({'run':r['run'],'n':len(live),'passed':len(live)-len(failed),'failed_ids':failed})
 payload={'schema_version':1,'status':'BUDGET_LIMITED_SHOWCASE_PARTIAL_GENERATION',
  'timestamp_utc':datetime.now(timezone.utc).isoformat(),'app_source_fingerprint':fingerprint,
  'dataset_fingerprint':dataset,'baseline_file':'baseline_results.json','baseline_sha256':baseline_sha,
  'scope':'Explicit user 30-minute scope override on 2026-10-16. Summarizes existing evidence only; original exhaustive final evaluation was not completed.',
  'full_final_suite_complete':False,'canonical_final_results_written':False,'new_inference_calls':0,
  'original_measurement_files_unchanged':True,'generation_coverage':coverage,'metrics':metrics,
  'paired_retrieval_tests':paired_significance(sources,'final',permutations=20000,draws=5000),
  'partial_generation_telemetry':telemetry,'security_live_probes':security,'sources':provenance,
  'confidence_note':'Selected metrics only. Frozen percentile bootstrap, 5,000 draws, seed741; repeated runs cluster by question/probe ID. Degenerate intervals and small synthetic samples do not establish population guarantees. Prefix CIs are conditional on the stopped prefix, not representative multimodal accuracy.',
  'not_measured':['External RAGAS LLM-judge scores: NOT MEASURED; separately named bounded Codex review is reported below.',
    'Full generation final pair, cross-run final variance and three-pass consistency: stopped by user budget.',
    'Final RAGAS embedding similarity/BERTScore: reference postprocessing was not reached.',
    'Scanned-PDF generation quality: no scanned questions in the stopped prefix.',
    'HTTP timeout rate, production capacity/cost, numeric trust calibration and isolated3D FPS: not established.']}
 review=collect_review(app/'evaluation')
 write_review(out,review)
 bind_review(payload,review)
 augment(payload,runs,baseline)
 save(out/'showcase_results.json',payload)
 render(out,payload)
 assert sha(baseline_path)==baseline_sha,'Baseline changed'
 print(json.dumps({'status':payload['status'],'metrics':len(metrics),'generation_questions':len(rows),'output':'showcase_results.json','baseline_unchanged':True}))


def render(out,data):
 lookup={m['metric']:m for m in data['metrics']}
 def point(m):
  if not m:return '—'
  return num(m['value'])
 def ci(m):
  c=m['ci95'];return '['+num(c['low'])+', '+num(c['high'])+']'if c.get('status')=='MEASURED'else 'NOT MEASURED'
 def n(m):return '/'.join(str(v)for v in m['n_per_run'])
 def block(names,heading,note):
  lines=['','### '+heading,'',note,'','| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |','| --- | --- | --- | --- | --- |']
  for name in names:
   m=lookup[name];lines.append(f'| `{esc(name)}` | {point(m.get("baseline"))} | {point(m)} | {n(m)} | {ci(m)} |')
  return lines
 c=data['generation_coverage'];t=data['partial_generation_telemetry']
 lines=['# HomeAtlas RAG showcase: measured results and limits','',
  '**Budget-limited report — the exhaustive final evaluation is incomplete.** On 2026-10-16 the user explicitly limited remaining work to 30 minutes. No new model calls were made for this report. Completed component pairs are shown alongside one stopped generation prefix; this is not a complete final multimodal accuracy score.','',
  f'Generation coverage: **{c["saved_questions"]}/{c["planned_questions_per_run"]} questions in run 1**, {c["answerable"]} answerable and {c["negative"]} negative; run 2 and the third-pass sample were not executed. Modality counts: '+', '.join(f'{k}={v}'for k,v in c['by_modality'].items())+'. **No scanned-PDF generation questions.** The prefix is deterministic, not randomly sampled.','',
  f'Application source: `{data["app_source_fingerprint"]}`. Dataset: `{data["dataset_fingerprint"]}`. Assembly UTC: `{data["timestamp_utc"]}`. Raw metric IDs, per-run values/n, source paths and CIs: [showcase_results.json](showcase_results.json).','',
  '## Headline scorecard',
  'Values are rates in [0,1] unless stated otherwise. Paired component columns average two independent runs; `n per run` lists each denominator, not a doubled independent sample. Generation uses only its saved prefix. Gold citation metrics assess source/page provenance, not semantic factual correctness.']
 if data.get('independent_review'):
  d=data['independent_review']['overall'];a=d['answerable_correctness'];neg=d['appropriate_negative_abstention'];h=d['hallucination_all_reviewed'];f=d['false_refusal_on_answerable']
  position=next(i for i,line in enumerate(lines)if line.startswith('Application source:'))
  lines[position:position]=[f'Independent Codex review of those saved answers: **answerable correctness {a["sum"]:g}/{a["n"]} = {a["mean"]:.6f}**, separate authored-negative abstention **{neg["count"]}/{neg["n"]}**; **{f["count"]}/{f["n"]} false refusal** and **{h["true_n"]}/{h["n"]} explicit hallucination flags**. Image answerable correctness is 6.5/10 and chart correctness 5/7. This bounded review is not RAGAS, human review, or production accuracy; exact denominators and failures are detailed below.','']
 lines+=block(SELECTED['retrieval-agent'][:5],'1. Retrieval at K=5',
  '**Precision, strict chunk recall, MRR and NDCG declined while hit rate improved.** All original gold and thresholds were retained. Page gold can include many OCR chunks: finding a relevant page does not establish extracted-answer coverage.')
 lines+=block(SELECTED['retrieval-agent'][5:],'2. Typo/Hinglish robustness',
  'Hybrid does not beat the best single channel on this typo subset. Fuzzy MRR already reaches the maximum on these synthetic questions; strict superiority is impossible on the same fixed sample.')
 lines+=block(SELECTED['ingestion-agent'][:2],'3. Scanned OCR',
  'Macro character/word error rates across four authored scanned pages; lower is better. These transcription errors are distinct from answer accuracy. Small synthetic-page coverage limits generalization.')
 lines+=block(SELECTED['ingestion-agent'][2:],'4. Table and chart ingestion',
  'Table cell text presence, structured parser output, and chart numeric-label text recall are separate. All table strings can be present while row/column structure is absent. Numeric label recall does not establish chart reasoning, captions or semantic figure understanding.')
 lines+=block(SELECTED['homeatlas-agent'][:5],'5. Household paths and source-value presence',
  'Identifier/date/amount rows total seven distinct source-value checks. Required-value presence is not automatic structured extraction or independently judged semantic correctness. Container coverage is only one case.')
 lines+=block(['E.aggregate_fact_presence'],'6. Aggregate questions',
  'The two source-listing questions contain required facts, but the receipt-total question lists individual amounts and omits the requested derived total. Fact presence does not establish complete aggregate answers.')
 lines+=block(SELECTED['homeatlas-agent'][6:],'7. Semantic cache and freshness',
  'Variant hits are below the requested 0.90 target; misses can still produce correct fallback answers. Zero false hits on ten near-miss probes does not prove a population false-hit rate below 2%. Move/delete invalidation uses two specific probes, not universal freshness coverage.')
 lines+=block(SELECTED['security-system-agent'],'8. Sensitive answer cache / security',
  'Zero persistence is observed for one synthetic sensitive-answer canary per run; this is not universal PII detection or zero leakage. Private process logs were not read. Frozen cache-isolation probes use the now-bypassed answer and do not establish populated-cache isolation.')
 for r in data['security_live_probes']:
  lines += [f'Live security run {r["run"]}: {r["passed"]}/{r["n"]} probes passed; failed IDs: '+', '.join('`'+esc(id)+'`'for id in r['failed_ids'])+'.']
 lines+=['','Those failures reflect frozen sensitive-answer retention assumptions after the privacy bypass. The raw evaluator retains static baseline `NOT_MET` privacy prose; the table follows the measured persistence value. Separate non-sensitive populated-cache regressions have a different scope and are not substituted into these scores.']
 lines+=block(SELECTED['generation-agent'][:7],'9. Partial generation: citation provenance and abstention',
  f'**Only {c["saved_questions"]} saved run-1 questions; {c["answerable"]} answerable / {c["negative"]} negative, no scans.** No full-baseline comparison is shown because coverage differs. Exact quotation/page provenance is not independent claim faithfulness or answer correctness. False refusal is measured among answerable questions; abstention recall is measured among negatives.')
 lines+=['','Additional partial wording diagnostics retained for audit: '+', '.join('`'+name+'`='+point(lookup[name])+' (n='+n(lookup[name])+')'for name in ['token_f1','rouge_l'])+'. Short references penalize verbose valid answers; these are not semantic correctness scores.',
  '','### 10. Partial latency and timeout evidence','',
  f'Observed in-process total query wall time: p50 **{num(t["saved_query_total_seconds_p50"])} s**, p95 **{num(t["saved_query_total_seconds_p95"])} s**, n={t["n"]}. '+t['scope']]
 timeout=t.get('logged_timeout_evidence')
 if timeout:
  lines += [f'Documented logged timeout: {timeout["logged_timeout_warnings"]} warning, saved question `{timeout["saved_generation_timeout_question"]}`, observed generation stage {num(timeout["observed_generation_seconds"])} s. This is evidence within {t["n"]} saved questions, not a count of all attempted HTTP requests.']
 lines+=['','HTTP timeout rate: **NOT MEASURED**. '+t['http_timeout_rate']['reason'],
  '',t['wrapper_counter_note'],
  '','## What remains unmeasured','']+['- '+s for s in data['not_measured']]
 lines+=['','## Reproduce the summary and inspect evidence','',
  'The summary helper reads existing results only. It does not run the application, change metrics/gold, call a model, overwrite the frozen baseline, or create a canonical `final_results.json`.',
  '','```sh','evaluation/.venv/bin/python evaluation/showcase/report.py --app-root "$PWD"','```','',
  'Selected intervals use the frozen 5,000-draw percentile bootstrap, seed741, with repeated runs clustered by question/probe ID. A degenerate [0,0] or [1,1] empirical interval is not a population guarantee. Prefix intervals are conditional on the stopped prefix, not representative multimodal quality. Superseded candidate runs remain in raw `candidate_history` and are excluded from this primary source version.',
  '', 'Known historical provenance limit: the baseline security metadata digest was captured before generation metadata finalized; its reused stage-call/timing rows match. Raw baseline objects are preserved. The actual records and model identities remain in [specialist results](results/).',
  '', '[Unchanged historical metric CSV](stats-metric-scorecard.csv) · [Frozen baseline JSON](baseline_results.json) · [Fix log](CHANGELOG.md)','']
 if data.get('independent_review'):
  lines+=['']+review_markdown(data['independent_review'])
 lines+=coverage_markdown(data)
 (out/'RAG_EVALUATION_REPORT.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
