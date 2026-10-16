"""Explicit requested-metric inventory from saved observations; no model calls."""
from statistics import mean
from stats_analysis import generation_samples
from independent_review import fmt_score, fmt_rate, support_label
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
 unjudged={'Context precision@5':'No independent scoring of the full ranked top-five context sets; answer judgments and retrieval overlap are not substitutes.',
  'Context recall':'No independent enumeration and scoring of all required contextual facts.',
  'Claim-count citation precision/recall':'Existing Codex judgments are categorical per answer, without enumerated claim counts.',
  'External RAGAS LLM-judge scores':'No external RAGAS judge calls; separately named bounded Codex review metrics are not substituted.'}
 data['requested_unmeasured']=[{'request':name,'value':None,'n':0,'status':'NOT MEASURED','reason':reason}for name,reason in unjudged.items()]
 if data.get('independent_review'):
  data['requested_independent_review']={'source':'results/independent-judge-summary.json','scope':'43/60 stopped synthetic generation questions; no scanned generation; no RAGAS/human/production claim'}
 else:
  data['requested_unmeasured'] += [{'request':name,'value':None,'n':0,'status':'NOT MEASURED','reason':'No independent review artifacts bound to this report.'}for name in ['Faithfulness / groundedness','Answer correctness','Answer relevancy','Hallucination rate','Semantic chart/image understanding','Per-answer citation claim support']]
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
 if data.get('independent_review'):
  d=data['independent_review']['overall'];v=data['independent_review']['visual_answerable'];h=d['hallucination_all_reviewed'];a=d['appropriate_negative_abstention']
  rows += [['Answer correctness — bounded Codex review, answerable only',fmt_score(d['answerable_correctness'])],
   ['Authored-negative appropriate abstention — bounded Codex review',fmt_rate(a['count'],a['n'])],
   ['Faithfulness / groundedness — bounded Codex review',fmt_score(d['faithfulness'])],
   ['Answer relevancy — bounded Codex review',fmt_score(d['answer_relevancy'])],
   ['Hallucination flags — bounded Codex review',fmt_rate(h['true_n'],h['n'])+'; all reviewed answers, including negatives'],
   ['Semantic chart/image answers — bounded Codex review',fmt_score(v['answerable_correctness'])+'; answerable visual correctness, not a broad visual-understanding benchmark'],
   ['Per-answer citation claim support — bounded Codex review',support_label(d['citation_claim_support_per_response'])+'; no claim-count precision/recall']]
 for m in data['requested_unmeasured']:rows.append([m['request'],'NOT MEASURED — '+m['reason']])
 p=data['requested_latency_binding'];rows.append(['p95 latency',num(p['value'])+' seconds (n='+str(p['n'])+'). '+p['definition']])
 lines+=['']+table(['Requested metric','Observed value / explicit unavailability'],rows)
 lines+=['','### Retrieval by modality at K=5','',
 'Complete paired component runs; n is answerable questions per run. Retrieval text includes household text scenarios plus PDF text; generation text below covers only the PDF prefix, so their denominators differ. Source/page gold maps to chunks and does not prove extracted-answer or semantic context coverage.']
 rows=[]
 for mod in MODS:rows.append([mod,look[f'{mod}/hybrid_runtime/recall@5']['n_per_run'][0]]+[num(look[f'{mod}/hybrid_runtime/{field}@5']['value'])for field in FIELDS])
 lines+=['']+table(['Modality','n/run','Precision@5','Recall@5','Hit@5','MRR@5','NDCG@5'],rows)
 lines+=['','### Generation by modality — stopped run 1 only','',
 'Citation columns are source/chunk/page provenance, not judged claim accuracy. Abstention recall uses saved negatives; false refusal uses saved answerable questions. No final run2/three-pass sample and no scanned generation questions.']
 rows=[]
 for mod,d in data['per_modality_coverage'].items():
  rows.append([mod,d['saved_generation_questions']]+[num(d['generation'][name]['value'])+' (n='+str(d['generation'][name]['n'])+')'for name in ['citation_gold_precision','citation_gold_recall','citation_gold_page_recall','abstention_recall','false_refusal_rate']])
 lines+=['']+table(['Modality','Saved','Citation precision','Citation chunk recall','Citation page recall','Abstention recall','False refusal'],rows)
 lines+=['','### Requested semantic metrics by modality — bounded independent review','',
 'Scores below mechanically aggregate existing Codex judgments, with nulls excluded and shown. Answer correctness uses answerable questions only; authored negatives appear separately. This is not RAGAS, human review, or production accuracy. Exact semantic context precision@5/recall and claim-count citation precision/recall remain unmeasured.']
 rows=[]
 review=data.get('independent_review')
 if review:
  for label,key in [('Answer correctness — answerable only','answerable_correctness'),('Faithfulness / groundedness','faithfulness'),('Answer relevancy','answer_relevancy')]:
   rows.append([label]+[fmt_score(review['by_modality'][mod][key])for mod in MODS])
  for label,key,count in [('Authored-negative appropriate abstention','appropriate_negative_abstention','count'),('Hallucination flags — all reviewed','hallucination_all_reviewed','true_n'),('False refusal — answerable only','false_refusal_on_answerable','count')]:
   rows.append([label]+[fmt_rate(review['by_modality'][mod][key][count],review['by_modality'][mod][key]['n'])for mod in MODS])
  rows.append(['Per-answer citation claim support']+[support_label(review['by_modality'][mod]['citation_claim_support_per_response'])if review['by_modality'][mod]['reviewed_n']else'NOT MEASURED (n=0)'for mod in MODS])
  rows.append(['Semantic chart/image answers']+['Not a visual modality','Not a visual modality',fmt_score(review['by_modality']['image']['answerable_correctness']),fmt_score(review['by_modality']['chart']['answerable_correctness']),'NOT MEASURED (n=0)'])
 for name in ['Context precision@5','Context recall','Claim-count citation precision/recall','External RAGAS LLM-judge scores']:
  rows.append([name]+['NOT MEASURED']*5)
 lines+=['']+table(['Metric','Text','Table','Image','Chart','Scanned'],rows)
 lines+=['','Currency cost/query is NOT MEASURED for every modality: local hardware/energy were not instrumented. Literal image-label recall and chart numeral recall do not establish semantic understanding; the separately named bounded visual review above evaluates only saved answers. Raw negative unsupported-answer metrics are distinct from the independent reviewer hallucination flags.']
 return lines
