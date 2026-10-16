"""Explicit requested-metric inventory from saved observations; no model calls."""
from statistics import mean
from stats_analysis import generation_samples
MODS=['text','table','image','chart','scanned']
FIELDS=['precision','recall','hit','mrr','ndcg']

def augment(data,runs,baseline):
 look={m['metric']:m for m in data['metrics']}; base={(m['agent'],m['metric']):m for m in baseline['metrics']}
 added={'retrieval-agent':[f'{mod}/hybrid_runtime/{field}@5'for mod in MODS for field in FIELDS]+['cross_modal/source_page_hit@5','cross_modal/text_modality_hit@5'],
 'homeatlas-agent':['E.room_accuracy','E.zone_accuracy','H.semantic_hit_rate','H.item_move_delete_freshness'],
 'ingestion-agent':['image.literal_label_recall'],
 'generation-agent':['abstention_precision','negative_answer_rate']+[f'{key}__{mod}'for mod in MODS[:-1]for key in ['citation_gold_precision','citation_gold_recall','citation_gold_page_recall']]}
 for agent,names in added.items():
  for name in names:
   if name in look:continue
   points=[next(m for m in r['metrics']if m['metric']==name)for r in runs[agent]]
   row={'agent':agent,'metric':name,'phase':'final','value':mean(m['value']for m in points),'run_values':[m['value']for m in points],
    'n_per_run':[m['n']for m in points],'n_runs':len(points),'status':'MEASURED','reason':None,
    'ci95':{'status':'NOT MEASURED','reason':'Additional coverage points only under the user time budget; no extra bootstrap requested.'},
    'scope':'stopped generation prefix'if agent=='generation-agent'else'completed paired component observations',
    'source_refs':[{'file':'results/'+agent+'.json','phase':'final','run':r['run'],'metric_id':name,'value':m['value'],'n':m['n']}for r,m in zip(runs[agent],points)],
    'baseline':None if agent=='generation-agent'else base.get((agent,name))}
   look[name]=row;data['metrics'].append(row)
 unjudged=['Context precision@5','Context recall','Faithfulness / groundedness','Answer correctness','Answer relevancy','Hallucination rate','Semantic chart/image understanding','Claim-level citation accuracy']
 data['requested_unmeasured']=[{'request':name,'value':None,'n':0,'status':'NOT MEASURED','reason':'No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts.'}for name in unjudged]
 data['requested_unmeasured'].append({'request':'Currency cost per query','value':None,'n':0,'status':'NOT MEASURED','reason':'Local hardware, energy and amortization cost were not instrumented; token telemetry is not currency cost.'})
 gen=runs['generation-agent'][0];matrix={}
 for mod in MODS:
  cells={}
  for name in ['citation_gold_precision','citation_gold_recall','citation_gold_page_recall']:
   m=look.get(name+'__'+mod);cells[name]={'value':m['value'],'n':m['n_per_run'][0],'source_refs':m['source_refs']}if m else{'value':None,'n':0,'reason':'No saved scanned-generation questions.'}
  for name in ['abstention_recall','false_refusal_rate']:
   samples=generation_samples(gen,name+'__'+mod)or[]
   cells[name]={'value':mean(s['value']for s in samples)if samples else None,'n':len(samples),
    'definition':'Frozen conditional abstention mean, scoped to saved modality rows; raw metrics unchanged.',
    'source_refs':{'file':'results/generation-agent.json','phase':'final','run':1,'field':'per_question.metrics.abstained','modality':mod,'sample_ids':[s['id']for s in samples]},
    'reason':None if samples else'No applicable saved questions.'}
  matrix[mod]={'saved_generation_questions':sum(q['modality']==mod for q in gen['per_question']),'generation':cells}
 data['per_modality_coverage']=matrix
 data['requested_metric_inventory']={
  'Recall@5':['all/hybrid_runtime/recall@5'],'Precision@5':['all/hybrid_runtime/precision@5'],'Hit@5':['all/hybrid_runtime/hit@5'],'MRR@5':['all/hybrid_runtime/mrr@5'],'NDCG@5':['all/hybrid_runtime/ndcg@5'],
  'Citation accuracy — source provenance only':['citation_gold_precision','citation_gold_recall','citation_gold_page_recall'],
  'Abstention / not found':['abstention_precision','abstention_recall','false_refusal_rate'],
  'OCR CER/WER':['ocr.scanned.cer_macro','ocr.scanned.wer_macro'],
  'Table extraction':['table.cell_text_recall','table.structured_output_rate'],
  'Chart/image literal diagnostics — not understanding':['chart.numeric_label_text_recall','image.literal_label_recall'],
  'Cross-modal retrieval hit':['cross_modal/source_page_hit@5','cross_modal/text_modality_hit@5'],
  'Location room/zone/container':['E.room_accuracy','E.zone_accuracy','E.container_accuracy'],
  'Typo / spelling':['typo/hybrid_runtime/mrr@5','typo/fuzzy/mrr@5'],
  'Cache hit / false hit / stale answers':['H.exact_hit_rate','H.semantic_hit_rate','H.near_miss_false_hit_rate','H.move_delete_invalidation','H.item_move_delete_freshness']}
 data['requested_latency_binding']={'request':'p95 latency','value':data['partial_generation_telemetry']['saved_query_total_seconds_p95'],'n':data['partial_generation_telemetry']['n'],'source':'results/generation-agent.json final run1 per_question.timings.total_seconds','definition':'Linear p95 of saved-prefix in-process wall times; not an HTTP SLA.'}

def coverage_markdown(data):
 def num(v):return 'NOT MEASURED'if v is None else f'{v:.6g}'
 def table(headers,rows):return ['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v).replace('|','\\|')for v in row)+' |'for row in rows]
 look={m['metric']:m for m in data['metrics']}
 lines=['','## Requested metric coverage','',
 'Every requested metric is explicitly measured with scope or marked NOT MEASURED with a reason. Judged context precision/recall, faithfulness, correctness, relevancy and hallucination are not retrieval or quotation proxies. Additional coverage points below retain original values/n; their extra CIs were not computed under the time budget.']
 rows=[]
 for request,names in data['requested_metric_inventory'].items():
  rows.append([request,'; '.join('`'+name+'`='+num(look[name]['value'])+' (n/run='+ '/'.join(map(str,look[name]['n_per_run']))+')'for name in names)])
 for m in data['requested_unmeasured']:rows.append([m['request'],'NOT MEASURED — '+m['reason']])
 p=data['requested_latency_binding'];rows.append(['p95 latency',num(p['value'])+' seconds (n='+str(p['n'])+'). '+p['definition']])
 lines+=['']+table(['Requested metric','Observed value / explicit unavailability'],rows)
 lines+=['','### Retrieval by modality at K=5','',
 'Complete paired component runs; n is answerable questions per run. Source/page gold maps to chunks and does not prove extracted-answer or semantic context coverage.']
 rows=[]
 for mod in MODS:rows.append([mod,look[f'{mod}/hybrid_runtime/recall@5']['n_per_run'][0]]+[num(look[f'{mod}/hybrid_runtime/{field}@5']['value'])for field in FIELDS])
 lines+=['']+table(['Modality','n/run','Precision@5','Recall@5','Hit@5','MRR@5','NDCG@5'],rows)
 lines+=['','### Generation by modality — stopped run 1 only','',
 'Citation columns are source/chunk/page provenance, not judged claim accuracy. Abstention recall uses saved negatives; false refusal uses saved answerable questions. No final run2/three-pass sample and no scanned generation questions.']
 rows=[]
 for mod,d in data['per_modality_coverage'].items():
  rows.append([mod,d['saved_generation_questions']]+[num(d['generation'][name]['value'])+' (n='+str(d['generation'][name]['n'])+')'for name in ['citation_gold_precision','citation_gold_recall','citation_gold_page_recall','abstention_recall','false_refusal_rate']])
 lines+=['']+table(['Modality','Saved','Citation precision','Citation chunk recall','Citation page recall','Abstention recall','False refusal'],rows)
 lines+=['','### Requested semantic metrics by modality — unmeasured','',
 'J = no independent judge scoring (zero judged samples); S = no saved scanned-generation questions. No lexical, label or citation-validity proxy is substituted. Context precision@5 also lacks a judged top-five context evaluation.']
 rows=[[m['request']]+['NOT MEASURED (J)']*4+['NOT MEASURED (S/J)']for m in data['requested_unmeasured']if m['request']!='Currency cost per query']
 lines+=['']+table(['Metric','Text','Table','Image','Chart','Scanned'],rows)
 lines+=['','Currency cost/query is NOT MEASURED for every modality: local hardware/energy were not instrumented. Literal image-label recall and chart numeral recall above do not establish semantic chart/image understanding. Negative unsupported-answer rate, if inspected in raw metrics, is not an independently judged hallucination rate.']
 return lines
