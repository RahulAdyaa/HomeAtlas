# HomeAtlas RAG showcase: measured results and limits

**Budget-limited report — the exhaustive final evaluation is incomplete.** On 2026-10-16 the user explicitly limited remaining work to 30 minutes. No new model calls were made for this report. Completed component pairs are shown alongside one stopped generation prefix; this is not a complete final multimodal accuracy score.

Generation coverage: **43/60 questions in run 1**, 37 answerable and 6 negative; run 2 and the third-pass sample were not executed. Modality counts: text=12, table=12, image=12, chart=7. **No scanned-PDF generation questions.** The prefix is deterministic, not randomly sampled.

Application source: `b253dd629e6ab18415e3bccf0448566e123f81907f631daa1407b51b588c95c8`. Dataset: `0bf5aba28055da78843f3a973c1886f79624dd3909bb48c6c032f3986c543fda`. Assembly UTC: `2026-10-16T06:22:45.099685+00:00`. Raw metric IDs, per-run values/n, source paths and CIs: [showcase_results.json](showcase_results.json).

## Headline scorecard
Values are rates in [0,1] unless stated otherwise. Paired component columns average two independent runs; `n per run` lists each denominator, not a doubled independent sample. Generation uses only its saved prefix. Gold citation metrics assess source/page provenance, not semantic factual correctness.

### 1. Retrieval at K=5

**Precision, strict chunk recall, MRR and NDCG declined while hit rate improved.** All original gold and thresholds were retained. Page gold can include many OCR chunks: finding a relevant page does not establish extracted-answer coverage.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `all/hybrid_runtime/precision@5` | 0.338843 | 0.287603 | 121/121 | [0.259504, 0.317355] |
| `all/hybrid_runtime/recall@5` | 0.8323 | 0.804924 | 121/121 | [0.744146, 0.863292] |
| `all/hybrid_runtime/mrr@5` | 0.930854 | 0.92011 | 121/121 | [0.877135, 0.958678] |
| `all/hybrid_runtime/ndcg@5` | 0.8955 | 0.855013 | 121/121 | [0.810089, 0.897308] |
| `all/hybrid_runtime/hit@5` | 0.975207 | 0.983471 | 121/121 | [0.958678, 1] |

### 2. Typo/Hinglish robustness

Hybrid does not beat the best single channel on this typo subset. Fuzzy MRR already reaches the maximum on these synthetic questions; strict superiority is impossible on the same fixed sample.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `typo/hybrid_runtime/mrr@5` | 0.965789 | 0.965789 | 38/38 | [0.910526, 1] |
| `typo/fuzzy/mrr@5` | 1 | 1 | 38/38 | [1, 1] |

### 3. Scanned OCR

Macro character/word error rates across four authored scanned pages; lower is better. These transcription errors are distinct from answer accuracy. Small synthetic-page coverage limits generalization.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `ocr.scanned.cer_macro` | 0.00337838 | 0.00337838 | 4/4 | [0, 0.0101351] |
| `ocr.scanned.wer_macro` | 0.0217391 | 0.0217391 | 4/4 | [0, 0.0652174] |

### 4. Table and chart ingestion

Table cell text presence, structured parser output, and chart numeric-label text recall are separate. All table strings can be present while row/column structure is absent. Numeric label recall does not establish chart reasoning, captions or semantic figure understanding.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `table.cell_text_recall` | 1 | 1 | 48/48 | [1, 1] |
| `table.structured_output_rate` | 0 | 0 | 4/4 | [0, 0] |
| `chart.numeric_label_text_recall` | 0.75 | 0.75 | 12/12 | [0.5, 1] |

### 5. Household paths and source-value presence

Identifier/date/amount rows total seven distinct source-value checks. Required-value presence is not automatic structured extraction or independently judged semantic correctness. Container coverage is only one case.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `E.full_path_accuracy` | 1 | 1 | 20/20 | [1, 1] |
| `E.container_accuracy` | 1 | 1 | 1/1 | [1, 1] |
| `E.document_identifier_fact_presence` | 1 | 1 | 3/3 | [1, 1] |
| `E.document_date_fact_presence` | 1 | 1 | 2/2 | [1, 1] |
| `E.document_amount_fact_presence` | 1 | 1 | 2/2 | [1, 1] |

### 6. Aggregate questions

The two source-listing questions contain required facts, but the receipt-total question lists individual amounts and omits the requested derived total. Fact presence does not establish complete aggregate answers.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `E.aggregate_fact_presence` | 0.333333 | 0.666667 | 3/3 | [0, 1] |

### 7. Semantic cache and freshness

Variant hits are below the requested 0.90 target; misses can still produce correct fallback answers. Zero false hits on ten near-miss probes does not prove a population false-hit rate below 2%. Move/delete invalidation uses two specific probes, not universal freshness coverage.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `H.exact_hit_rate` | 1 | 1 | 5/5 | [1, 1] |
| `H.variant_hit_rate` | 0.8 | 0.8 | 10/10 | [0.5, 1] |
| `H.variant_answer_accuracy` | 1 | 1 | 10/10 | [1, 1] |
| `H.variant_correct_answer_hit_rate` | 0.8 | 0.8 | 10/10 | [0.5, 1] |
| `H.near_miss_false_hit_rate` | 0 | 0 | 10/10 | [0, 0] |
| `H.move_delete_invalidation` | 1 | 1 | 2/2 | [1, 1] |

### 8. Sensitive answer cache / security

Zero persistence is observed for one synthetic sensitive-answer canary per run; this is not universal PII detection or zero leakage. Private process logs were not read. Frozen cache-isolation probes use the now-bypassed answer and do not establish populated-cache isolation.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `sensitive_answer_cache_persistence_rate` | 1 | 0 | 1/1 | [0, 0] |
Live security run 1: 24/27 probes passed; failed IDs: `cache-own-exact-hit-A`, `cache-second-user-own-hit`, `cache-stored-content-policy`.
Live security run 2: 24/27 probes passed; failed IDs: `cache-own-exact-hit-A`, `cache-second-user-own-hit`, `cache-stored-content-policy`.

Those failures reflect frozen sensitive-answer retention assumptions after the privacy bypass. The raw evaluator retains static baseline `NOT_MET` privacy prose; the table follows the measured persistence value. Separate non-sensitive populated-cache regressions have a different scope and are not substituted into these scores.

### 9. Partial generation: citation provenance and abstention

**Only 43 saved run-1 questions; 37 answerable / 6 negative, no scans.** No full-baseline comparison is shown because coverage differs. Exact quotation/page provenance is not independent claim faithfulness or answer correctness. False refusal is measured among answerable questions; abstention recall is measured among negatives.

| Metric ID | Baseline | Current observed | n per run | 95% empirical CI |
| --- | --- | --- | --- | --- |
| `citation_gold_precision` | — | 0.936937 | 37 | [0.867117, 0.986486] |
| `citation_gold_recall` | — | 0.585023 | 37 | [0.446481, 0.722973] |
| `citation_gold_f1` | — | 0.630781 | 37 | [0.505773, 0.754501] |
| `citation_gold_page_recall` | — | 0.972973 | 37 | [0.918919, 1] |
| `citation_exact_quote_rate` | — | 1 | 36 | [1, 1] |
| `false_refusal_rate` | — | 0.027027 | 37 | [0, 0.0810811] |
| `abstention_recall` | — | 1 | 6 | [1, 1] |

Additional partial wording diagnostics retained for audit: `token_f1`=0.193313 (n=37), `rouge_l`=0.189762 (n=37). Short references penalize verbose valid answers; these are not semantic correctness scores.

### 10. Partial latency and timeout evidence

Observed in-process total query wall time: p50 **94.8424 s**, p95 **162.591 s**, n=43. Observed in-process total query wall time on a shared development host; includes resource waits and same-run resumability effects. Not HTTP end-to-end latency or a production SLA.
Documented logged timeout: 1 warning, saved question `text-12`, observed generation stage 150.432 s. This is evidence within 43 saved questions, not a count of all attempted HTTP requests.

HTTP timeout rate: **NOT MEASURED**. Completed-response usage and saved question rows do not enumerate every attempted HTTP request. Logged timeout evidence is reported separately.

generation_model_calls and verification_model_calls count wrapper invocations, not actual HTTP requests. Numeric guards may return before HTTP; usage proves completed responses only.

## What remains unmeasured

- Independent-judge faithfulness/semantic correctness/hallucination rate: no external judge credential.
- Full generation final pair, cross-run final variance and three-pass consistency: stopped by user budget.
- Final RAGAS embedding similarity/BERTScore: reference postprocessing was not reached.
- Scanned-PDF generation quality: no scanned questions in the stopped prefix.
- HTTP timeout rate, production capacity/cost, numeric trust calibration and isolated3D FPS: not established.

## Reproduce the summary and inspect evidence

The summary helper reads existing results only. It does not run the application, change metrics/gold, call a model, overwrite the frozen baseline, or create a canonical `final_results.json`.

```sh
evaluation/.venv/bin/python evaluation/showcase/report.py --app-root "$PWD"
```

Selected intervals use the frozen 5,000-draw percentile bootstrap, seed741, with repeated runs clustered by question/probe ID. A degenerate [0,0] or [1,1] empirical interval is not a population guarantee. Prefix intervals are conditional on the stopped prefix, not representative multimodal quality. Superseded candidate runs remain in raw `candidate_history` and are excluded from this primary source version.

Known historical provenance limit: the baseline security metadata digest was captured before generation metadata finalized; its reused stage-call/timing rows match. Raw baseline objects are preserved. The actual records and model identities remain in [specialist results](results/).

[Full historical baseline report](RAG_EVALUATION_BASELINE_APPENDIX.md) · [Unchanged historical metric CSV](stats-metric-scorecard.csv) · [Frozen baseline JSON](baseline_results.json) · [Fix log](CHANGELOG.md)


## Requested metric coverage

Every requested metric is explicitly measured with scope or marked NOT MEASURED with a reason. Judged context precision/recall, faithfulness, correctness, relevancy and hallucination are not retrieval or quotation proxies. Additional coverage points below retain original values/n; their extra CIs were not computed under the time budget.

| Requested metric | Observed value / explicit unavailability |
| --- | --- |
| Recall@5 | `all/hybrid_runtime/recall@5`=0.804924 (n/run=121/121) |
| Precision@5 | `all/hybrid_runtime/precision@5`=0.287603 (n/run=121/121) |
| Hit@5 | `all/hybrid_runtime/hit@5`=0.983471 (n/run=121/121) |
| MRR@5 | `all/hybrid_runtime/mrr@5`=0.92011 (n/run=121/121) |
| NDCG@5 | `all/hybrid_runtime/ndcg@5`=0.855013 (n/run=121/121) |
| Citation accuracy — source provenance only | `citation_gold_precision`=0.936937 (n/run=37); `citation_gold_recall`=0.585023 (n/run=37); `citation_gold_page_recall`=0.972973 (n/run=37) |
| Abstention / not found | `abstention_precision`=0.857143 (n/run=7); `abstention_recall`=1 (n/run=6); `false_refusal_rate`=0.027027 (n/run=37) |
| OCR CER/WER | `ocr.scanned.cer_macro`=0.00337838 (n/run=4/4); `ocr.scanned.wer_macro`=0.0217391 (n/run=4/4) |
| Table extraction | `table.cell_text_recall`=1 (n/run=48/48); `table.structured_output_rate`=0 (n/run=4/4) |
| Chart/image literal diagnostics — not understanding | `chart.numeric_label_text_recall`=0.75 (n/run=12/12); `image.literal_label_recall`=1 (n/run=24/24) |
| Cross-modal retrieval hit | `cross_modal/source_page_hit@5`=1 (n/run=5/5); `cross_modal/text_modality_hit@5`=0.4 (n/run=5/5) |
| Location room/zone/container | `E.room_accuracy`=1 (n/run=20/20); `E.zone_accuracy`=1 (n/run=20/20); `E.container_accuracy`=1 (n/run=1/1) |
| Typo / spelling | `typo/hybrid_runtime/mrr@5`=0.965789 (n/run=38/38); `typo/fuzzy/mrr@5`=1 (n/run=38/38) |
| Cache hit / false hit / stale answers | `H.exact_hit_rate`=1 (n/run=5/5); `H.semantic_hit_rate`=0.8 (n/run=10/10); `H.near_miss_false_hit_rate`=0 (n/run=10/10); `H.move_delete_invalidation`=1 (n/run=2/2); `H.item_move_delete_freshness`=1 (n/run=2/2) |
| Context precision@5 | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Context recall | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Faithfulness / groundedness | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Answer correctness | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Answer relevancy | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Hallucination rate | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Semantic chart/image understanding | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Claim-level citation accuracy | NOT MEASURED — No independent semantic judge scoring; retrieval overlap, literal labels, source quotation and refusal behavior are not substitutes. Context precision@5 additionally requires judged top-five contexts. |
| Currency cost per query | NOT MEASURED — Local hardware, energy and amortization cost were not instrumented; token telemetry is not currency cost. |
| p95 latency | 162.591 seconds (n=43). Linear p95 of saved-prefix in-process wall times; not an HTTP SLA. |

### Retrieval by modality at K=5

Complete paired component runs; n is answerable questions per run. Source/page gold maps to chunks and does not prove extracted-answer or semantic context coverage.

| Modality | n/run | Precision@5 | Recall@5 | Hit@5 | MRR@5 | NDCG@5 |
| --- | --- | --- | --- | --- | --- | --- |
| text | 81 | 0.209877 | 0.975309 | 0.975309 | 0.911523 | 0.926731 |
| table | 10 | 0.22 | 1 | 1 | 1 | 1 |
| image | 10 | 0.42 | 0.25 | 1 | 0.8 | 0.475105 |
| chart | 10 | 0.58 | 0.20625 | 1 | 0.95 | 0.688811 |
| scanned | 10 | 0.56 | 0.383333 | 1 | 1 | 0.675227 |

### Generation by modality — stopped run 1 only

Citation columns are source/chunk/page provenance, not judged claim accuracy. Abstention recall uses saved negatives; false refusal uses saved answerable questions. No final run2/three-pass sample and no scanned generation questions.

| Modality | Saved | Citation precision | Citation chunk recall | Citation page recall | Abstention recall | False refusal |
| --- | --- | --- | --- | --- | --- | --- |
| text | 12 | 0.9 (n=10) | 0.9 (n=10) | 0.9 (n=10) | 1 (n=2) | 0.1 (n=10) |
| table | 12 | 1 (n=10) | 1 (n=10) | 1 (n=10) | 1 (n=2) | 0 (n=10) |
| image | 12 | 0.916667 (n=10) | 0.15 (n=10) | 1 (n=10) | 1 (n=2) | 0 (n=10) |
| chart | 7 | 0.928571 (n=7) | 0.16369 (n=7) | 1 (n=7) | NOT MEASURED (n=0) | 0 (n=7) |
| scanned | 0 | NOT MEASURED (n=0) | NOT MEASURED (n=0) | NOT MEASURED (n=0) | NOT MEASURED (n=0) | NOT MEASURED (n=0) |

### Requested semantic metrics by modality — unmeasured

J = no independent judge scoring (zero judged samples); S = no saved scanned-generation questions. No lexical, label or citation-validity proxy is substituted. Context precision@5 also lacks a judged top-five context evaluation.

| Metric | Text | Table | Image | Chart | Scanned |
| --- | --- | --- | --- | --- | --- |
| Context precision@5 | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Context recall | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Faithfulness / groundedness | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Answer correctness | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Answer relevancy | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Hallucination rate | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Semantic chart/image understanding | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |
| Claim-level citation accuracy | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (J) | NOT MEASURED (S/J) |

Currency cost/query is NOT MEASURED for every modality: local hardware/energy were not instrumented. Literal image-label recall and chart numeral recall above do not establish semantic chart/image understanding. Negative unsupported-answer rate, if inspected in raw metrics, is not an independently judged hallucination rate.