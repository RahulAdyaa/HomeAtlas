# Hybrid retrieval and cache evaluation

Model: `intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3`. Actual PostgreSQL channels, fictional 20-document corpus. No personal records.

68 queries, 38 typo/Hinglish variants; K=5. Gold labels declared in `hybrid_testset.py`.

| Subset | Channel | Recall@5 | Precision@5 | MRR@5 | NDCG@5 |
|---|---|---:|---:|---:|---:|
| overall | dense | 1.000 | 0.200 | 0.984 | 0.988 |
| overall | word | 0.905 | 0.181 | 0.862 | 0.873 |
| overall | fuzzy | 1.000 | 0.200 | 1.000 | 1.000 |
| overall | hybrid | 1.000 | 0.200 | 1.000 | 1.000 |
| typo | dense | 1.000 | 0.200 | 0.987 | 0.990 |
| typo | word | 0.842 | 0.168 | 0.772 | 0.790 |
| typo | fuzzy | 1.000 | 0.200 | 1.000 | 1.000 |
| typo | hybrid | 1.000 | 0.200 | 1.000 | 1.000 |
| identifier | dense | 1.000 | 0.200 | 1.000 | 1.000 |
| identifier | word | 1.000 | 0.200 | 1.000 | 1.000 |
| identifier | fuzzy | 1.000 | 0.200 | 1.000 | 1.000 |
| identifier | hybrid | 1.000 | 0.200 | 1.000 | 1.000 |

Hybrid strictly beats every single channel on typo MRR: **False**. Ties are not wins. This small synthetic corpus can saturate recall; shared aliases help all channels. We do not alter gold labels or claim production accuracy from this benchmark.

## No-match retrieval

| Channel | Empty top-5 rate |
|---|---:|
| dense | 80.0% |
| word | 80.0% |
| fuzzy | 80.0% |
| hybrid | 80.0% |

Retrieval candidates are not answers: the evidence verifier must abstain when a retrieved record does not answer the question. No-match retrieval failures are explicitly retained in the results.

## Semantic cache

Variant hit rate: **100.0%** (35 queries, target ≥90%). Near-miss false-hit rate: **0.0%** (20 queries, target <2%).

| Mode | Mean latency (ms) | Generation calls |
|---|---:|---:|
| Cache off | 11814.3 | 4 |
| Primed cache on | 10.7 | 0 |

Off measures parallel retrieval + generation/verification; on measures cache lookup. Two repeats with loaded models; cache priming excluded. HTTP/auth/credit accounting excluded.
Generation modes: ['local-model-explained', 'local-model-explained']. Calls count actual local LLM HTTP requests, including evidence verification.

Automated DB tests separately check move/delete freshness, stale writes, user/household isolation, bypass, expiry and LRU. Cache guard intentionally prefers misses for uncertain spellings; threshold remains 0.93. Low semantic similarity or unmatched key terms explain variant misses; inspect the JSON for individual cases.
