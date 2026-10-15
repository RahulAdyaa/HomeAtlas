> Historical baseline: image extraction and source-image generation have since changed. Current image regression results are in [IMAGE_PIPELINE_REPORT.md](IMAGE_PIPELINE_REPORT.md); the original measurements below are preserved.

# HomeAtlas multimodal RAG evaluation

**Status: partial evaluation, 60/60 questions executed. Overall semantic-quality score: unavailable.** Seven required RAGAS judge metrics and free-tier visual judging could not run because no credential is configured. Missing scores are null, never imputed as passing or zero. No application logic or household data was changed.

**Observed operational diagnostic index: 84.9%**, equal mean of four disclosed measurements: extraction token completeness, final recall@5, reference-term coverage and negative abstention. This is 4/4 diagnostic inputs, **not** a comprehensive quality score or replacement for RAGAS. Required judge metric coverage: 0/420 question-metric observations; answer-similarity coverage: 60/60.

## Summary scorecard

| Component | Score/status | Interpretation |
|---|---|---|
| Parsing: text token completeness | 100.0% | 20 pages; visual semantics excluded |
| Parsing: page assignment | 100.0% | Chunk text matches independent source-page transcript |
| OCR WER | 0.0% | Lower is better; authored scan transcription |
| Table cell text availability | 100.0% | Flat cell token presence, not structure |
| Table structure preservation | 0.0% | No structured table output |
| Figure detection recall | 0.0% | No figure detector; page previews are not detections |
| Retrieval recall@5 | 84.6% | Answerable questions only |
| Generation: reference-term coverage | 55.0% | Deterministic diagnostic; NOT RAGAS correctness |
| RAGAS answer similarity | 64.3% | Actual RAGAS with app BGE embeddings |
| RAGAS judge metrics | N/A | Free-tier credentials missing for present run |
| Citation page/chunk accuracy | 96.7% | Conditional on emitted citations |
| Correct negative abstention | 100.0% | 10 negative questions |
| App clickable citations | N/A | Isolated core evaluation does not create authenticated source URLs |
| Trust numeric correlation | N/A | App exposes confidence labels, not requested numerical scores |
| Robustness | Measured | Four variants; two questions each |
| System | Measured | Local stage latency/usage; excludes HTTP upload/queue/DB |

## Setup, scope and reproducibility

Five original CC0 PDFs, four pages each, 60 independently authored questions: 12 per modality, 50 answerable and 10 unanswerable. Question types include factual, multi-chunk, cross-modal, summary, numeric/chart-reading and absent-evidence cases. Ground truth is authored from fixture specifications and the rendered scan sample was visually reviewed. Each question has source pages and mapped exact app chunk IDs. This small, clean synthetic corpus is a diagnostic benchmark, not a representative customer-data estimate.

The evaluator imports the **actual** app `extract`, `rank_candidates`, `answer_from_evidence`, and `LocalModels` implementations. It mirrors ingestion embedding attachment and uses an isolated in-memory corpus. It does not invoke the HTTP upload, queue, database authorization/credit transactions or browser citation viewer. Those are out of this measured scope; prior app audits are not counted here. All writes, fixtures, dependency additions and caches reside under evaluation.

| Model | Identity |
|---|---|
| text | BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a |
| image | google/siglip2-base-patch16-224@75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2 |
| reranker | BAAI/bge-reranker-base@2cfc18c9415c912f9d8155881c133215df768a70 |
| generation | qwen3-vl:4b-instruct |

Python 3.12; PyMuPDF, Tesseract OCR, NumPy, Torch/Transformers and RAGAS 0.2.15. Seed 741, local generation temperature 0; app does not set an Ollama inference seed, so cold generative repeats are not guaranteed bitwise identical. Completed model outputs are cached. Model revisions match the app. requirements.lock.txt pins the installed environment; app dependencies are read-only. Free judge supports OpenRouter free IDs only; actual returned provider/model and usage are saved in cache when configured.

## Modality comparison

| Modality | N | Recall@5 | Term coverage | RAGAS similarity | Abstention on negatives |
|---|---|---|---|---|---|
| text | 12 | 100.0% | 90.0% | 81.6% | 100.0% |
| table | 12 | 100.0% | 90.0% | 67.1% | 100.0% |
| image | 12 | 85.0% | 0.0% | 45.8% | 100.0% |
| chart | 12 | 100.0% | 0.0% | 42.8% | 100.0% |
| scanned | 12 | 38.0% | 95.0% | 84.1% | 100.0% |

Image/chart semantic understanding is the measured weak point: PDF pages with native headers enter the native-text branch; text inside embedded raster figures is not OCRed. Page previews receive image embeddings but no figure captions or structured chart values are created. The ordinary text-query generator receives retrieved text, **not the source page images**. Thus retrieving the right page is insufficient to answer visual questions. No external judge interpretation is counted as an app capability.

## 1. Parsing and OCR

| Modality | Text completeness | Page assignment | CER | WER | Chunks | Ingestion s/page |
|---|---|---|---|---|---|---|
| text | 100.0% | 100.0% | N/A | N/A | 4 | 1.452 |
| table | 100.0% | 100.0% | N/A | N/A | 4 | 0.105 |
| image | 100.0% | 100.0% | N/A | N/A | 4 | 0.098 |
| chart | 100.0% | 100.0% | N/A | N/A | 4 | 0.100 |
| scanned | 100.0% | 100.0% | 0.0% | 0.0% | 20 | 0.420 |

Text completeness measures authored native text (or OCR transcription) token recall; it deliberately excludes diagram/chart raster text and cannot establish semantic completeness. Page assignment requires normalized chunk text to occur in the independently authored matching source-page transcript; identical repeated lines can be ambiguous. Citation correctness additionally matches independently annotated question source pages. OCR sample is the four authored image-only pages with saved reference/extracted text in results.json.

| Table page | Cell text availability | Structured cell accuracy | Rows/columns preserved |
|---|---|---|---|
| 1 | 100.0% | 0.0% | 0.0% |
| 2 | 100.0% | 0.0% | 0.0% |
| 3 | 100.0% | 0.0% | 0.0% |
| 4 | 100.0% | 0.0% | 0.0% |

Cell text availability checks exact cell strings in flattened page output, not whether the system relates each value to its correct header. Structured cell accuracy is zero because the app emits no table cell coordinates or row/column object. Eight expected figures (four diagrams/four charts), zero dedicated detections; rendered whole-page previews have 100% page coverage but do not count as figure detection.

## 2. Image and chart understanding

Caption correctness/completeness/invented-details rubric: **unsupported app stage**, because no image caption/description output exists to score. Free-tier visual judging of generated visual answers: **blocked by missing credential**. Chart value/trend/axis/legend questions are included in per-question results and reference-term diagnostics. Semantic chart-reading accuracy and image-description hallucination rates remain unavailable without a judge and/or an app description output; safe abstention is reported separately.

| Chart question | Term coverage | Mode |
|---|---|---|
| chart-01 | 0.0% | abstention |
| chart-02 | 0.0% | abstention |
| chart-03 | 0.0% | abstention |
| chart-04 | 0.0% | abstention |
| chart-05 | 0.0% | abstention |
| chart-06 | 0.0% | abstention |
| chart-07 | 0.0% | abstention |
| chart-08 | 0.0% | abstention |
| chart-09 | 0.0% | local-model-grounded |
| chart-10 | 0.0% | abstention |

## 3. Chunking

| Modality | Min chars | Median chars | Max chars | Chunks |
|---|---|---|---|---|
| text | 257 | 257.0 | 257 | 4 |
| table | 147 | 147.0 | 148 | 4 |
| image | 36 | 36.0 | 36 | 4 |
| chart | 36 | 36.0 | 36 | 4 |
| scanned | 21 | 27.0 | 38 | 20 |

The app groups native blocks up to 1200 characters within a page and emits OCR lines separately. It never merges evidence across pages. Multi-page questions therefore require multiple chunks; the generator permits at most two short quotes, which limits four-page summaries. Tables remain within one page chunk here but flatten header/cell relationships. Figure+caption semantic pairs are absent, not merely split. These short fixtures do not stress the 1200-character boundary; this is a coverage limitation.

## 4–6. Retrieval and reranking

Gold relevance is the set of exact chunks on independently annotated relevant pages, including page preview carriers. This is **page-grounded relevance**, not a claim every chunk contains the answer. Scans have several relevant page chunks, so chunk recall is strict; evidence-term availability is independently reported. Unanswerable questions are excluded from ranking averages. The app returns at most five final chunks; @10 uses denominator 10 and does not fabricate extra results. Before-rerank comparison uses the same five-result budget; full 16 candidate IDs are retained in raw JSON.

### overall

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 80.0% | 59.0% | 80.0% | 80.0% | 80.0% | 59.0% |
| 3 | 40.0% | 72.8% | 86.0% | 82.0% | 79.2% | 68.8% |
| 5 | 27.6% | 84.6% | 98.0% | 84.7% | 79.9% | 72.0% |
| 10 | 13.8% | 84.6% | 98.0% | 84.7% | 78.7% | 72.0% |

### text

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 100.0% | 87.5% | 100.0% | 100.0% | 100.0% | 87.5% |
| 3 | 43.3% | 97.5% | 100.0% | 100.0% | 100.0% | 97.5% |
| 5 | 28.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 10 | 14.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

### table

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| 3 | 36.7% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 5 | 22.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 10 | 11.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

### image

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| 3 | 10.0% | 30.0% | 30.0% | 10.0% | 15.0% | 10.0% |
| 5 | 18.0% | 85.0% | 90.0% | 23.5% | 37.9% | 22.2% |
| 10 | 9.0% | 85.0% | 90.0% | 23.5% | 37.9% | 22.2% |

### chart

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| 3 | 36.7% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 5 | 22.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 10 | 11.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

### scanned

| K | Precision | Recall | Hit rate | MRR | NDCG | MAP@K |
|---|---|---|---|---|---|---|
| 1 | 100.0% | 17.5% | 100.0% | 100.0% | 100.0% | 17.5% |
| 3 | 73.3% | 36.5% | 100.0% | 100.0% | 81.2% | 36.5% |
| 5 | 48.0% | 38.0% | 100.0% | 100.0% | 61.6% | 38.0% |
| 10 | 24.0% | 38.0% | 100.0% | 100.0% | 55.5% | 38.0% |

| Ranking (K=5) | Precision | Recall | Hit | MRR | NDCG | MAP@5 |
|---|---|---|---|---|---|---|
| Before rerank (fusion top five) | 28.8% | 87.7% | 100.0% | 93.3% | 88.0% | 81.6% |
| After rerank and production filter | 27.6% | 84.6% | 98.0% | 84.7% | 79.9% | 72.0% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| Overall | 28.6% | 84.6% | 72.0% |

Cross-modal text queries: source modality hit@5 98.0%. Per-question top-K modality mixtures are recorded in JSON using both ground-truth source modality and the app-emitted modality. Native table/image/chart pages are labeled text by the app; this distinction is retained.

| Image query source | Correct source page hit@5 | Correct text chunk hit@5 | Returned app modalities |
|---|---|---|---|
| text | 100.0% | 100.0% | {"text": 5} |
| table | 100.0% | 100.0% | {"text": 5} |
| image | 100.0% | 100.0% | {"text": 4, "ocr": 1} |
| chart | 100.0% | 100.0% | {"text": 5} |
| scanned | 100.0% | 0.0% | {"ocr": 5} |

## 7. RAGAS generation evaluation

| Metric | Mean | Scored questions |
|---|---|---|
| faithfulness | N/A | 0 |
| answer_relevancy | N/A | 0 |
| context_precision | N/A | 0 |
| context_recall | N/A | 0 |
| answer_correctness | N/A | 0 |
| answer_similarity | 64.3% | 60 |
| multimodal_faithfulness | N/A | 0 |
| multimodal_relevance | N/A | 0 |

All eight metrics use RAGAS implementations; answer similarity runs locally with the app’s BGE model. Seven judge-dependent metrics are null without OPENROUTER_API_KEY. The evaluator uses actual RAGAS MultiModalFaithfulness/MultiModalRelevance with retrieved text and local page image paths; the judge can inspect retrieved images, but this does not mean the app generator saw them. Retry/backoff, bounded HTTP errors, raw response cache and per-metric cache support resuming. The judge integration is import-checked but live external calls are unverified because credentials are absent.

## 8. Citations and visual grounding

Conditional citation source/page/chunk accuracy: 96.7%. Answerable questions with at least one correct emitted citation: 58.0%. Visual bbox/page-region match: 96.7%. These are local metadata/exact quote checks. The app’s authenticated clickable citation URL/browser navigation is **not tested** by this isolated corpus; no synthetic link is substituted for a real app URL.

## 9. Trust metrics

The app returns categorical confidence (`supported`, `insufficient`, `conflicting`) and optional owner diagnostics, not numeric relevance/correctness/authenticity trust scores. Therefore requested numerical correlation/calibration is unsupported. Relevance is an internal reranker score rather than answer correctness. Confidence labels are retained for each question; negative abstention agreement is measured below, but is not a proxy for three missing scores.

## 10. Negative cases

Correct abstention: 100.0% (10/10). Non-abstention on absent evidence: 0.0%. Questions include an undocumented purple valve; any answer on those is flagged in raw results. Non-abstention is a diagnostic failure, not automatically a hallucinated fact. Semantic hallucination rate remains judge-blocked. Exact-copy citation validation prevents invented quoted text but does not prove relevance or correctness.

## 11. Robustness

| Variant | CER | WER | Mean term coverage | Drop vs original |
|---|---|---|---|---|
| low_resolution | 0.0% | 0.0% | 100.0% | 0.0% |
| rotated_90 | 112.8% | 260.0% | 0.0% | 100.0% |
| blur_noise | 206.1% | 424.0% | 0.0% | 100.0% |
| mixed_language | 0.0% | 0.0% | 100.0% | 0.0% |

Each variant replaces scan page 1 in the full corpus and reruns the same two pressure/date questions: 300×375 low-resolution resampling, 90-degree rotation, Gaussian blur plus seeded noise, and mixed English/Spanish/French text. Drop is baseline reference-term coverage minus degraded coverage; negative drop means improvement. Mixed-language text is an added-language robustness check with the same English target facts, not a multilingual semantic benchmark. Changed pages use the same app text and image embeddings as baseline ingestion.

## 12. System metrics

| Modality | Stage | Mean seconds | p95 seconds |
|---|---|---|---|
| overall | retrieval | 0.534 | 1.453 |
| overall | generation | 1.277 | 1.968 |
| overall | total | 1.812 | 2.959 |
| text | retrieval | 0.927 | 3.994 |
| text | generation | 1.418 | 1.904 |
| text | total | 2.346 | 5.888 |
| table | retrieval | 0.365 | 0.459 |
| table | generation | 1.416 | 2.274 |
| table | total | 1.781 | 2.508 |
| image | retrieval | 0.386 | 0.499 |
| image | generation | 1.048 | 1.701 |
| image | total | 1.435 | 2.106 |
| chart | retrieval | 0.477 | 1.763 |
| chart | generation | 0.997 | 2.260 |
| chart | total | 1.474 | 2.770 |
| scanned | retrieval | 0.517 | 2.967 |
| scanned | generation | 1.505 | 1.968 |
| scanned | total | 2.023 | 4.672 |

| Instrumented call | Mean s | p95 s | Calls |
|---|---|---|---|
| text_embedding | 0.019 | 0.025 | 60 |
| image_embedding | 0.101 | 0.608 | 60 |
| reranking | 0.399 | 0.851 | 60 |
| generation | 1.274 | 1.965 | 60 |

Observed local generation usage: 21408 prompt tokens and 1736 generated tokens across 60 HTTP responses. These are observed Ollama counters, not estimates. Cached generation calls retain their original response result but may have no newly observed token response; raw question results preserve the initial usage. Judge usage is unavailable without credentials. End-to-end core timings include local extraction/retrieval/generation only, not network upload, queue wait, DB writes or UI rendering. Cached question rows retain original timings; per-call cache flags are in JSON.

## Top failures and per-question results

| ID | Modality/type | Term coverage | Reason |
|---|---|---|---|
| text-10 | text/summary | 0.0% | Abstained despite answerable source |
| table-10 | table/cross-modal | 0.0% | Abstained despite answerable source |
| image-01 | image/factual | 0.0% | Abstained despite answerable source |
| image-02 | image/factual | 0.0% | Abstained despite answerable source |
| image-03 | image/factual | 0.0% | Abstained despite answerable source |
| image-04 | image/factual | 0.0% | Abstained despite answerable source |
| image-05 | image/factual | 0.0% | Abstained despite answerable source |
| image-06 | image/factual | 0.0% | Abstained despite answerable source |
| image-07 | image/factual | 0.0% | Reference terms missing; inspect raw quote/context |
| image-08 | image/factual | 0.0% | Abstained despite answerable source |
| image-09 | image/multi-chunk | 0.0% | Abstained despite answerable source |
| image-10 | image/summary | 0.0% | Abstained despite answerable source |
| chart-01 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-02 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-03 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-04 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-05 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-06 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-07 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |
| chart-08 | chart/numeric/chart-reading | 0.0% | Abstained despite answerable source |

All 60 raw question outputs, references, exact chunk IDs, top-K metrics, modalities, timings, RAGAS statuses and citations are in results.json; results.csv is a compact analysis table. testset.json preserves authored source page/region annotations and exact mapped chunk IDs.

### Concrete failure examples

- **text-10**: Summarize the service inspection intervals for all four T units. Reference: T1: 3, T2: 4, T3: 5, T4: 6 months. Observed: The available records do not contain enough direct evidence to answer confidently.
- **table-09**: Give Boost power in table 1 and table 4. Reference: Table 1: 71 W; table 4: 74 W. Observed: These records may conflict; confirm the applicable version before relying on them.  “Boost 74 14” [1]  “Boost 71 11” [2]
- **image-07**: What cartridge identifier is shown in diagram 4? Reference: The cartridge is H400. Observed: Your records say:  “HomeAtlas evaluation: scanned record 4” [1]
- **chart-01**: What is March energy usage in chart 1? Reference: March usage is 65 kWh. Observed: The available records do not contain enough direct evidence to answer confidently.
- **scanned-10**: Summarize the inspection year and next inspection year for the pumps. Reference: Inspected in 2026; next inspection in 2027. Observed: Your records say:  “Next inspection: 2027.” [1]

## Prioritized recommendations

1. **P0 — visual evidence delivery:** extract embedded raster figures even on native-text pages, OCR their labels, retain figure regions/captions and pass retrieved source images into the vision generator. Keep exact citation validation and safe abstention.
2. **P0 — tables:** add structured row/column extraction with header associations and retain both structured text and source-region coordinates.
3. **P1 — multi-page answers:** evaluate expanding the two-quote cap and preserving facts across more than two retrieved chunks; use targeted summaries with clear citations.
4. **P1 — OCR robustness:** orientation correction, image preprocessing, multilingual OCR configuration, and page-level grouping.
5. **P1 — evaluation completion:** configure a free text/vision judge privately, resume all modalities, then review semantic correctness/faithfulness alongside diagnostics. Expand beyond clean synthetic records and include human-reviewed customer-like pages.
6. **P2 — retrieval/observability:** expose before/after retrieval diagnostics with explicit K, instrument token/stage usage, and distinguish retrieval similarity from answer trust. Add an isolated authenticated end-to-end evaluation environment for clickable citations/queue/upload timing.

## Formulas and limitations

Precision@K = relevant returned chunks / K (missing slots count nonrelevant). Recall@K = unique relevant returned / all relevant chunks. Hit@K = 1 when any relevant chunk is returned. MRR@K = reciprocal rank of first relevant hit or 0. DCG = sum(binary relevance/log2(rank+1)); NDCG divides by ideal DCG at K. AP@K = sum(precision at each relevant rank)/all relevant chunks; MAP averages AP over answerable questions. Final precision uses actual returned-set size; final MAP uses all returned chunks. No duplicate chunks receive extra credit.

CER = character Levenshtein distance / reference character count; WER = token Levenshtein distance / reference token count after lowercasing and whitespace normalization. OCR edit rates can exceed 100%. Text completeness = multiset reference word overlap / reference words. Cell content accuracy = cells whose exact text occurs on the matching page / annotated cells. Structured cell/row-column accuracy requires explicit app structural output; absent output yields 0. Figure recall = dedicated detected figures / annotated figures. Term coverage = matching independently authored answer tokens/terms / expected terms. It is not semantic accuracy. Source citation accuracy requires gold page/chunk and exact substring in that chunk. p95 uses nearest-rank ceil(0.95*n).

Limitations: 20 clean synthetic pages; diagram/chart figures deliberately rasterized, creating a useful but nonrepresentative modality challenge; no long-page boundary test; page-level gold mapping broadens chunk relevance; no external judge credentials; no app caption or table detector output; no numeric trust scores; no authenticated clickable citation verification; core in-memory pipeline only. These omissions are never claimed as passed.

## Re-run

See README.md. From the app root: `python evaluation/run_eval.py`. To resume one slice: `python evaluation/run_eval.py --modality chart`. Completed question/model caches are reused; configure evaluation/.env privately to resume missing judge metrics. No model downloads occur during evaluation.

## Primary references

- RAGAS metrics: https://docs.ragas.io/en/v0.2.15/concepts/metrics/available_metrics/
- RAGAS pinned implementation: https://github.com/explodinggradients/ragas/tree/v0.2.15/src/ragas/metrics
- OpenRouter free models: https://openrouter.ai/docs/guides/routing/model-variants/free
- App implementation: worker/ingestion.py, worker/models.py, worker/retrieval.py (read-only).

## Supplementary modality metrics

### text before/after reranking

| Stage | K | P | R | Hit | MRR | NDCG | MAP |
|---|---|---|---|---|---|---|---|
| Before (five-result budget) | 1 | 100.0% | 87.5% | 100.0% | 100.0% | 100.0% | 87.5% |
| Before (five-result budget) | 3 | 43.3% | 97.5% | 100.0% | 100.0% | 100.0% | 97.5% |
| Before (five-result budget) | 5 | 28.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Before (five-result budget) | 10 | 14.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 1 | 100.0% | 87.5% | 100.0% | 100.0% | 100.0% | 87.5% |
| After (actual final output) | 3 | 43.3% | 97.5% | 100.0% | 100.0% | 100.0% | 97.5% |
| After (actual final output) | 5 | 28.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 10 | 14.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| text | 31.0% | 100.0% | 100.0% |

### table before/after reranking

| Stage | K | P | R | Hit | MRR | NDCG | MAP |
|---|---|---|---|---|---|---|---|
| Before (five-result budget) | 1 | 90.0% | 85.0% | 90.0% | 90.0% | 90.0% | 85.0% |
| Before (five-result budget) | 3 | 36.7% | 100.0% | 100.0% | 95.0% | 96.3% | 95.0% |
| Before (five-result budget) | 5 | 22.0% | 100.0% | 100.0% | 95.0% | 96.3% | 95.0% |
| Before (five-result budget) | 10 | 11.0% | 100.0% | 100.0% | 95.0% | 96.3% | 95.0% |
| After (actual final output) | 1 | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| After (actual final output) | 3 | 36.7% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 5 | 22.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 10 | 11.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| table | 22.0% | 100.0% | 100.0% |

### image before/after reranking

| Stage | K | P | R | Hit | MRR | NDCG | MAP |
|---|---|---|---|---|---|---|---|
| Before (five-result budget) | 1 | 60.0% | 55.0% | 60.0% | 60.0% | 60.0% | 55.0% |
| Before (five-result budget) | 3 | 36.7% | 100.0% | 100.0% | 76.7% | 82.6% | 76.7% |
| Before (five-result budget) | 5 | 22.0% | 100.0% | 100.0% | 76.7% | 82.6% | 76.7% |
| Before (five-result budget) | 10 | 11.0% | 100.0% | 100.0% | 76.7% | 82.6% | 76.7% |
| After (actual final output) | 1 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| After (actual final output) | 3 | 10.0% | 30.0% | 30.0% | 10.0% | 15.0% | 10.0% |
| After (actual final output) | 5 | 18.0% | 85.0% | 90.0% | 23.5% | 37.9% | 22.2% |
| After (actual final output) | 10 | 9.0% | 85.0% | 90.0% | 23.5% | 37.9% | 22.2% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| image | 18.0% | 85.0% | 22.2% |

### chart before/after reranking

| Stage | K | P | R | Hit | MRR | NDCG | MAP |
|---|---|---|---|---|---|---|---|
| Before (five-result budget) | 1 | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| Before (five-result budget) | 3 | 36.7% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Before (five-result budget) | 5 | 22.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Before (five-result budget) | 10 | 11.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 1 | 100.0% | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| After (actual final output) | 3 | 36.7% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 5 | 22.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| After (actual final output) | 10 | 11.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| chart | 22.0% | 100.0% | 100.0% |

### scanned before/after reranking

| Stage | K | P | R | Hit | MRR | NDCG | MAP |
|---|---|---|---|---|---|---|---|
| Before (five-result budget) | 1 | 90.0% | 15.5% | 90.0% | 90.0% | 90.0% | 15.5% |
| Before (five-result budget) | 3 | 70.0% | 34.5% | 100.0% | 95.0% | 76.5% | 33.5% |
| Before (five-result budget) | 5 | 50.0% | 38.5% | 100.0% | 95.0% | 60.9% | 36.3% |
| Before (five-result budget) | 10 | 25.0% | 38.5% | 100.0% | 95.0% | 54.3% | 36.3% |
| After (actual final output) | 1 | 100.0% | 17.5% | 100.0% | 100.0% | 100.0% | 17.5% |
| After (actual final output) | 3 | 73.3% | 36.5% | 100.0% | 100.0% | 81.2% | 36.5% |
| After (actual final output) | 5 | 48.0% | 38.0% | 100.0% | 100.0% | 61.6% | 38.0% |
| After (actual final output) | 10 | 24.0% | 38.0% | 100.0% | 100.0% | 55.5% | 38.0% |

| Final set | Precision | Recall | MAP |
|---|---|---|---|
| scanned | 50.0% | 38.0% | 38.0% |

| Modality | Call stage | Mean s | p95 s |
|---|---|---|---|
| text | text_embedding | 0.012 | 0.023 |
| text | image_embedding | 0.287 | 0.893 |
| text | reranking | 0.624 | 3.071 |
| text | generation | 1.415 | 1.901 |
| table | text_embedding | 0.013 | 0.024 |
| table | image_embedding | 0.042 | 0.077 |
| table | reranking | 0.306 | 0.376 |
| table | generation | 1.412 | 2.271 |
| image | text_embedding | 0.017 | 0.030 |
| image | image_embedding | 0.042 | 0.052 |
| image | reranking | 0.324 | 0.438 |
| image | generation | 1.045 | 1.698 |
| chart | text_embedding | 0.039 | 0.298 |
| chart | image_embedding | 0.088 | 0.608 |
| chart | reranking | 0.346 | 0.851 |
| chart | generation | 0.994 | 2.257 |
| scanned | text_embedding | 0.014 | 0.026 |
| scanned | image_embedding | 0.045 | 0.100 |
| scanned | reranking | 0.394 | 2.119 |
| scanned | generation | 1.502 | 1.965 |

## Single-page evidence splitting diagnostic

| Modality | Questions | All terms present somewhere | Terms split across chunks | Split rate among present |
|---|---|---|---|---|
| text | 8 | 8 | 0 | 0.0% |
| table | 9 | 9 | 0 | 0.0% |
| image | 9 | 0 | 0 | N/A |
| chart | 9 | 0 | 0 | N/A |
| scanned | 8 | 8 | 0 | 0.0% |

This exact-term diagnostic only covers authored single-page evidence. Absent visual terms are reported as absent, not as a favorable zero split rate. Multi-page questions are intentionally excluded.
