# HomeAtlas multimodal RAG evaluation

Completed phase: **baseline**. Assembly timestamp: `2026-10-15T12:33:30.003434+00:00`. All values below are generated from specialist result files. Missing measurements remain null with reasons.

## Frozen scope and provenance

The frozen corpus contains 5 original synthetic CC0 PDFs (20 pages), 60 PDF questions, 20 fictional household documents and 78 household questions: 138 questions in total. The retrieval suite has 121 answerable questions and 17 negatives; the generation suite has 50 answerable PDF questions and 10 negatives. Supplemental upload, cache, security and degraded-image probes report their own denominators. These suites are not interchangeable.

- Dataset fingerprint: `0bf5aba28055da78843f3a973c1886f79624dd3909bb48c6c032f3986c543fda`.
- App source fingerprint: `e89dd896bea27ebdf4ac879f91549f28c82c4004f7ffbb7b9b8c41fa68b08b25`.
- Judge model: **NOT MEASURED — no free-tier judge credential was configured**. Local generation is not an independent judge. No paid fallback was used.
- Each inference specialist ran two actual independent passes. A generation response from run 1 cannot satisfy run 2; run-scoped resumability is distinct from a new inference pass.
- Source hashes, model revisions, timestamps and raw run digests are retained in [baseline_results.json](baseline_results.json). Final application evaluation is not complete yet.

| Specialist | Run | Application commit | Timestamp UTC |
| --- | --- | --- | --- |
| generation-agent | 1 | `26386903934c4283a70e83868dfc888952273171` | 2026-10-15T08:55:04.030535+00:00 |
| generation-agent | 2 | `1786a84fa492bc43dd44573f95d9ec683774d115` | 2026-10-15T12:30:14.393591+00:00 |
| homeatlas-agent | 1 | `d7e2f21cb29e9ef9c8a87d698273049d1f617ca5` | 2026-10-15T07:46:04.232496+00:00 |
| homeatlas-agent | 2 | `d7e2f21cb29e9ef9c8a87d698273049d1f617ca5` | 2026-10-15T07:53:37.516564+00:00 |
| ingestion-agent | 1 | `17bc806955e1610997fe05dfdd9879a689e8c83b` | 2026-10-15T11:51:33.239009+00:00 |
| ingestion-agent | 2 | `17bc806955e1610997fe05dfdd9879a689e8c83b` | 2026-10-15T11:52:11.597123+00:00 |
| retrieval-agent | 1 | `57b84946dd1c15653a9c5be649006af247d71035` | 2026-10-15T07:21:29.316495+00:00 |
| retrieval-agent | 2 | `57b84946dd1c15653a9c5be649006af247d71035` | 2026-10-15T07:23:04.045791+00:00 |
| security-system-agent | 1 | `9ebfb0a3c29d3b39b5bb8d8ed13bc5198f72e43f` | 2026-10-15T12:22:50.760551+00:00 |
| security-system-agent | 2 | `9ebfb0a3c29d3b39b5bb8d8ed13bc5198f72e43f` | 2026-10-15T12:22:52.833496+00:00 |
| testset-agent | 1 | `5f33a9b157a4394e60f3bac0ede95d293f5bf3fc` | 2026-10-15T07:06:17.675740+00:00 |

Evaluation-only commits can differ between specialists; the application source hash is authoritative. The input audit runs once because it checks immutable files rather than performing model inference.

## Statistical method

Point estimates are equal means of the two independent per-run scorecards. The 95% percentile bootstrap uses 5000 resamples and seed 741. Question/probe IDs are resampled jointly across repeated runs, so two observations of one question do not become two independent questions. Sample standard deviation uses the two run scores (denominator runs − 1). Intervals describe this small synthetic question distribution, not a guarantee about real household documents. A one-probe degenerate interval is explicitly weak evidence.

A confidence interval is computed only if raw sample counts and the specified estimator reproduce both published point estimates. Otherwise its status and reason appear in the complete scorecard. Descriptive totals, extrema, missing numeric confidences and unsupported estimators are never assigned invented intervals. A zero-failure sample can produce a degenerate [0,0] bootstrap interval; it does not prove a zero population failure rate. In particular, zero false hits on the ten near-miss probes cannot establish the requested population rate below 2%. Repeated runs of those same probes do not double the number of independent probes. Conditional denominators (for example, answers containing citations) are retained. Every metric and its n/run, run variance, interval status and reason is in [stats-metric-scorecard.csv](stats-metric-scorecard.csv).

### Paired hybrid versus strongest single channel

The strongest dense/word/fuzzy channel is selected on these observed questions, separately for each measure and subset. These are exploratory comparisons, not held-out model selection. Paired two-sided sign permutation uses question-averaged run scores; exact enumeration is used when feasible, otherwise seeded Monte Carlo with a plus-one correction. Holm correction covers all eight displayed tests. Positive difference favors runtime hybrid.

| Phase | Subset | Measure @5 | n | Best single | Hybrid | Single | Difference [95% CI] | p (two-sided) | p (Holm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | all | precision | 121 | fuzzy | 0.338843 | 0.266116 | 0.0727273 [0.0396694, 0.112397] | 9.9995e-05 | 0.00079996 |
| baseline | all | recall | 121 | fuzzy | 0.8323 | 0.78478 | 0.0475207 [0.0147986, 0.0826446] | 0.00484976 | 0.0339483 |
| baseline | all | mrr | 121 | fuzzy | 0.930854 | 0.909091 | 0.0217631 [-0.0289325, 0.0738292] | 0.417829 | 1 |
| baseline | all | ndcg | 121 | fuzzy | 0.8955 | 0.850615 | 0.0448842 [-0.00103123, 0.0934058] | 0.0684966 | 0.410979 |
| baseline | typo | precision | 38 | fuzzy | 0.2 | 0.2 | 0 [0, 0] | 1 | 1 |
| baseline | typo | recall | 38 | fuzzy | 1 | 1 | 0 [0, 0] | 1 | 1 |
| baseline | typo | mrr | 38 | fuzzy | 0.965789 | 1 | -0.0342105 [-0.0894737, 0] | 0.5 | 1 |
| baseline | typo | ndcg | 38 | fuzzy | 0.974152 | 1 | -0.0258478 [-0.0678311, 0] | 0.5 | 1 |

**The target “hybrid beats every single channel on the typo subset” is not met.** The table retains measures where the strongest single channel ties or outperforms hybrid. Ranks and per-question paired differences remain available for diagnosis.

## A/G: retrieval, typo robustness and cross-modal search

Runtime output is capped at 5; diagnostic top-10 runs are explicitly named. Precision divides by requested K even if fewer results return. AP@K divides by total relevant chunks; R-Precision@K uses the first min(K,R) results divided by R. Frozen PDF gold marks all chunks on an authored relevant page, so fixed-K chunk recall has a ceiling on pages with many OCR chunks. A page hit does not establish that the answer facts were extracted. Source-page and literal evidence diagnostics are reported separately.

### Channel comparison and K=1/3/5/10

The strongest single channel already achieves the maximum MRR on this typo sample. Strictly beating that value is impossible on the same fixed sample; tying it still does not satisfy the requested strict-superiority target.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `all/dense/f1@1` | 0.656991 (95% CI [0.579202, 0.734522]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/f1@10` | 0.200471 (95% CI [0.18353, 0.217883]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/f1@3` | 0.426298 (95% CI [0.392542, 0.458263]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/f1@5` | 0.320189 (95% CI [0.297136, 0.342945]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/hit@1` | 0.801653 (95% CI [0.727273, 0.867769]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/hit@10` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/hit@3` | 0.900826 (95% CI [0.842975, 0.950413]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/hit@5` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/map@1` | 0.63688 (95% CI [0.556125, 0.718147]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/map@10` | 0.723101 (95% CI [0.656386, 0.789536]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/map@3` | 0.70687 (95% CI [0.636101, 0.776862]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/map@5` | 0.718061 (95% CI [0.6503, 0.786272]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/mrr@1` | 0.801653 (95% CI [0.727273, 0.867769]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/mrr@10` | 0.851515 (95% CI [0.793382, 0.906336]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/mrr@3` | 0.849862 (95% CI [0.790634, 0.904959]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/mrr@5` | 0.851515 (95% CI [0.793382, 0.906336]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/ndcg@1` | 0.801653 (95% CI [0.727273, 0.867769]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/ndcg@10` | 0.776513 (95% CI [0.716886, 0.833833]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/ndcg@3` | 0.818011 (95% CI [0.758141, 0.872854]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/ndcg@5` | 0.799738 (95% CI [0.742246, 0.85402]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/precision@1` | 0.801653 (95% CI [0.727273, 0.867769]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/precision@10` | 0.142149 (95% CI [0.122314, 0.164463]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/precision@3` | 0.38292 (95% CI [0.344353, 0.424242]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/precision@5` | 0.261157 (95% CI [0.231405, 0.292562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/r_precision@1` | 0.63688 (95% CI [0.556125, 0.718147]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/r_precision@10` | 0.701791 (95% CI [0.629817, 0.772043]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/r_precision@3` | 0.680441 (95% CI [0.605368, 0.754997]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/r_precision@5` | 0.695076 (95% CI [0.621212, 0.766878]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/recall@1` | 0.63688 (95% CI [0.556125, 0.718147]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/recall@10` | 0.771006 (95% CI [0.705058, 0.835572]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/recall@3` | 0.738292 (95% CI [0.667355, 0.807688]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/dense/recall@5` | 0.761191 (95% CI [0.694043, 0.827824]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/f1@1` | 0.731779 (95% CI [0.659722, 0.803874]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/f1@10` | 0.195742 (95% CI [0.181172, 0.21013]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/f1@3` | 0.456625 (95% CI [0.428079, 0.483252]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/f1@5` | 0.32737 (95% CI [0.306356, 0.347674]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/hit@1` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/hit@10` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/hit@3` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/hit@5` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/map@1` | 0.711433 (95% CI [0.634982, 0.788055]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/map@10` | 0.773416 (95% CI [0.70764, 0.837638]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/map@3` | 0.768595 (95% CI [0.702647, 0.832989]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/map@5` | 0.772383 (95% CI [0.706439, 0.836269]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/mrr@1` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/mrr@10` | 0.909091 (95% CI [0.859504, 0.954545]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/mrr@3` | 0.909091 (95% CI [0.859504, 0.954545]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/mrr@5` | 0.909091 (95% CI [0.859504, 0.954545]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/ndcg@1` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/ndcg@10` | 0.817965 (95% CI [0.760283, 0.872245]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/ndcg@3` | 0.894992 (95% CI [0.843006, 0.940706]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/ndcg@5` | 0.850615 (95% CI [0.796935, 0.899265]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/precision@1` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/precision@10` | 0.135537 (95% CI [0.119008, 0.15374]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/precision@3` | 0.429752 (95% CI [0.38292, 0.473829]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/precision@5` | 0.266116 (95% CI [0.236364, 0.295868]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/r_precision@1` | 0.711433 (95% CI [0.634982, 0.788055]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/r_precision@10` | 0.769284 (95% CI [0.702479, 0.83385]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/r_precision@3` | 0.76343 (95% CI [0.696281, 0.829545]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/r_precision@5` | 0.768251 (95% CI [0.701963, 0.833161]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/recall@1` | 0.711433 (95% CI [0.634982, 0.788055]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/recall@10` | 0.785813 (95% CI [0.721414, 0.848829]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/recall@3` | 0.779959 (95% CI [0.71436, 0.844008]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/fuzzy/recall@5` | 0.78478 (95% CI [0.720037, 0.847796]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/f1@1` | 0.709306 (95% CI [0.637009, 0.780597]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/f1@10` | 0.233713 (95% CI [0.212683, 0.255855]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/f1@3` | 0.465595 (95% CI [0.437095, 0.491866]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/f1@5` | 0.382992 (95% CI [0.354624, 0.412976]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/hit@1` | 0.909091 (95% CI [0.859298, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/hit@10` | 0.975207 (95% CI [0.942149, 1]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/hit@3` | 0.942149 (95% CI [0.900826, 0.983471]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/hit@5` | 0.975207 (95% CI [0.942149, 1]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/map@1` | 0.681818 (95% CI [0.604507, 0.758785]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/map@10` | 0.790535 (95% CI [0.730961, 0.848567]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/map@3` | 0.752281 (95% CI [0.685862, 0.816333]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/map@5` | 0.790535 (95% CI [0.730961, 0.848567]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/mrr@1` | 0.909091 (95% CI [0.859298, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/mrr@10` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/mrr@3` | 0.924242 (95% CI [0.87741, 0.965565]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/ndcg@1` | 0.909091 (95% CI [0.859298, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/ndcg@10` | 0.846978 (95% CI [0.800794, 0.890736]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/ndcg@3` | 0.909931 (95% CI [0.863109, 0.951242]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/ndcg@5` | 0.8955 (95% CI [0.855756, 0.930562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/precision@1` | 0.909091 (95% CI [0.859298, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/precision@10` | 0.169421 (95% CI [0.147934, 0.192562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/precision@3` | 0.46832 (95% CI [0.418733, 0.517906]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/precision@5` | 0.338843 (95% CI [0.295868, 0.385124]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/r_precision@1` | 0.681818 (95% CI [0.604507, 0.758785]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/r_precision@10` | 0.778581 (95% CI [0.71436, 0.839704]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/r_precision@3` | 0.746384 (95% CI [0.678202, 0.811983]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/r_precision@5` | 0.778581 (95% CI [0.71436, 0.839704]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/recall@1` | 0.681818 (95% CI [0.604507, 0.758785]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/recall@10` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/recall@3` | 0.762913 (95% CI [0.697301, 0.82593]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/f1@1` | 0.743716 (95% CI [0.673353, 0.813837]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/f1@10` | 0.204007 (95% CI [0.188479, 0.219861]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/f1@3` | 0.455122 (95% CI [0.426316, 0.482111]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/f1@5` | 0.328642 (95% CI [0.307299, 0.348976]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/hit@1` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/hit@10` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/hit@3` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/hit@5` | 0.933884 (95% CI [0.884298, 0.975207]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/map@1` | 0.721763 (95% CI [0.646522, 0.797004]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/map@10` | 0.783095 (95% CI [0.719388, 0.846002]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/map@3` | 0.773072 (95% CI [0.707128, 0.837986]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/map@5` | 0.778151 (95% CI [0.712894, 0.842114]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/mrr@1` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/mrr@10` | 0.921488 (95% CI [0.871901, 0.96281]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/mrr@3` | 0.921488 (95% CI [0.871901, 0.96281]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/mrr@5` | 0.921488 (95% CI [0.871901, 0.96281]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/ndcg@1` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/ndcg@10` | 0.829127 (95% CI [0.772935, 0.881559]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/ndcg@3` | 0.898965 (95% CI [0.847346, 0.944166]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/ndcg@5` | 0.856748 (95% CI [0.804219, 0.905322]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/precision@1` | 0.909091 (95% CI [0.85124, 0.958678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/precision@10` | 0.142975 (95% CI [0.124793, 0.16281]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/precision@3` | 0.426997 (95% CI [0.380165, 0.473829]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/precision@5` | 0.267769 (95% CI [0.238017, 0.299174]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/r_precision@1` | 0.721763 (95% CI [0.646522, 0.797004]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/r_precision@10` | 0.786846 (95% CI [0.724165, 0.848313]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/r_precision@3` | 0.770661 (95% CI [0.704029, 0.836273]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/r_precision@5` | 0.777548 (95% CI [0.71281, 0.841086]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/recall@1` | 0.721763 (95% CI [0.646522, 0.797004]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/recall@10` | 0.79511 (95% CI [0.732955, 0.855553]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/recall@3` | 0.778926 (95% CI [0.71383, 0.843492]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_text_diagnostic10/recall@5` | 0.785813 (95% CI [0.721242, 0.848321]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/f1@1` | 0.661072 (95% CI [0.580875, 0.737443]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/f1@10` | 0.194991 (95% CI [0.177234, 0.212636]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/f1@3` | 0.434837 (95% CI [0.401898, 0.466072]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/f1@5` | 0.310841 (95% CI [0.286187, 0.334588]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/hit@1` | 0.826446 (95% CI [0.760331, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/hit@10` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/hit@3` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/hit@5` | 0.884298 (95% CI [0.826446, 0.942149]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/map@1` | 0.639118 (95% CI [0.555785, 0.719013]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/map@10` | 0.715202 (95% CI [0.644713, 0.781827]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/map@3` | 0.707645 (95% CI [0.637048, 0.775659]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/map@5` | 0.710399 (95% CI [0.638946, 0.777897]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/mrr@1` | 0.826446 (95% CI [0.760331, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/mrr@10` | 0.853994 (95% CI [0.793388, 0.909091]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/mrr@3` | 0.853994 (95% CI [0.793388, 0.909091]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/mrr@5` | 0.853994 (95% CI [0.793388, 0.909091]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/ndcg@1` | 0.826446 (95% CI [0.760331, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/ndcg@10` | 0.766099 (95% CI [0.701807, 0.824528]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/ndcg@3` | 0.841913 (95% CI [0.780662, 0.896651]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/ndcg@5` | 0.793254 (95% CI [0.731349, 0.849293]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/precision@1` | 0.826446 (95% CI [0.760331, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/precision@10` | 0.138017 (95% CI [0.119008, 0.158678]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/precision@3` | 0.418733 (95% CI [0.369146, 0.46832]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/precision@5` | 0.256198 (95% CI [0.224793, 0.287603]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/r_precision@1` | 0.639118 (95% CI [0.555785, 0.719013]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/r_precision@10` | 0.702135 (95% CI [0.628607, 0.773248]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/r_precision@3` | 0.691116 (95% CI [0.615186, 0.763946]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/r_precision@5` | 0.693871 (95% CI [0.617936, 0.767222]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/recall@1` | 0.639118 (95% CI [0.555785, 0.719013]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/recall@10` | 0.745523 (95% CI [0.678715, 0.810438]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/recall@3` | 0.732438 (95% CI [0.663223, 0.7996]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/word/recall@5` | 0.735193 (95% CI [0.665461, 0.802867]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `typo/dense/f1@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/f1@10` | 0.172249 (95% CI [0.157895, 0.181818]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/f1@3` | 0.473684 (95% CI [0.434211, 0.5]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/f1@5` | 0.315789 (95% CI [0.289474, 0.333333]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/hit@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/hit@10` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/hit@3` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/hit@5` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/map@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/map@10` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/map@3` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/map@5` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/mrr@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/mrr@10` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/mrr@3` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/mrr@5` | 0.881579 (95% CI [0.789474, 0.960526]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/ndcg@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/ndcg@10` | 0.898807 (95% CI [0.810147, 0.970863]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/ndcg@3` | 0.898807 (95% CI [0.810147, 0.970863]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/ndcg@5` | 0.898807 (95% CI [0.810147, 0.970863]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/precision@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/precision@10` | 0.0947368 (95% CI [0.0868421, 0.1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/precision@3` | 0.315789 (95% CI [0.289474, 0.333333]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/precision@5` | 0.189474 (95% CI [0.173684, 0.2]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/r_precision@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/r_precision@10` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/r_precision@3` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/r_precision@5` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/recall@1` | 0.815789 (95% CI [0.684211, 0.921053]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/recall@10` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/recall@3` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/dense/recall@5` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/fuzzy/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/f1@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/f1@3` | 0.486842 (95% CI [0.460526, 0.5]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/hit@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/hit@3` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/map@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/map@10` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/map@3` | 0.960526 (95% CI [0.894737, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/map@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/mrr@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/mrr@10` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/mrr@3` | 0.960526 (95% CI [0.894737, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/ndcg@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/ndcg@10` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/ndcg@3` | 0.963972 (95% CI [0.901628, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/precision@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/precision@3` | 0.324561 (95% CI [0.307018, 0.333333]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/r_precision@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/r_precision@10` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/r_precision@3` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/r_precision@5` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/recall@1` | 0.947368 (95% CI [0.868421, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/recall@3` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_runtime/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/f1@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/hit@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/map@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/map@10` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/map@3` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/map@5` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/mrr@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/mrr@10` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/mrr@3` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/mrr@5` | 0.986842 (95% CI [0.960526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/ndcg@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/ndcg@10` | 0.990288 (95% CI [0.970863, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/ndcg@3` | 0.990288 (95% CI [0.970863, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/ndcg@5` | 0.990288 (95% CI [0.970863, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/precision@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/r_precision@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/r_precision@10` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/r_precision@3` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/r_precision@5` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/recall@1` | 0.973684 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/hybrid_text_diagnostic10/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/f1@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/f1@10` | 0.15311 (95% CI [0.129187, 0.172249]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/f1@3` | 0.421053 (95% CI [0.355263, 0.473684]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/f1@5` | 0.280702 (95% CI [0.236842, 0.315789]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/hit@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/hit@10` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/hit@3` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/hit@5` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/map@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/map@10` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/map@3` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/map@5` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/mrr@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/mrr@10` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/mrr@3` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/mrr@5` | 0.77193 (95% CI [0.644627, 0.881579]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/ndcg@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/ndcg@10` | 0.790098 (95% CI [0.664786, 0.898807]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/ndcg@3` | 0.790098 (95% CI [0.664786, 0.898807]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/ndcg@5` | 0.790098 (95% CI [0.664786, 0.898807]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/precision@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/precision@10` | 0.0842105 (95% CI [0.0710526, 0.0947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/precision@3` | 0.280702 (95% CI [0.236842, 0.315789]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/precision@5` | 0.168421 (95% CI [0.142105, 0.189474]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/r_precision@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/r_precision@10` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/r_precision@3` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/r_precision@5` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/recall@1` | 0.710526 (95% CI [0.552632, 0.842105]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/recall@10` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/recall@3` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/word/recall@5` | 0.842105 (95% CI [0.710526, 0.947368]; n=38 clusters; observations=76) | No completed phase | 0 / — |

### Per-modality runtime results

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `chart/hybrid_runtime/f1@5` | 0.312378 (95% CI [0.285033, 0.339496]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/map@5` | 0.20849 (95% CI [0.175469, 0.2375]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/mrr@5` | 0.95 (95% CI [0.85, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/ndcg@5` | 0.716538 (95% CI [0.704161, 0.722727]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/precision@5` | 0.62 (95% CI [0.6, 0.66]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/r_precision@5` | 0.2125 (95% CI [0.1875, 0.2375]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/recall@5` | 0.2125 (95% CI [0.1875, 0.2375]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chart/hybrid_runtime/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `household/hybrid_runtime/f1@5` | 0.325956 (95% CI [0.305164, 0.343394]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/hit@5` | 0.957746 (95% CI [0.901408, 1]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/map@5` | 0.896244 (95% CI [0.826761, 0.956338]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/mrr@5` | 0.896244 (95% CI [0.826761, 0.956338]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/ndcg@5` | 0.910963 (95% CI [0.848246, 0.963446]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/precision@5` | 0.197183 (95% CI [0.183099, 0.208451]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/r_precision@5` | 0.873239 (95% CI [0.788732, 0.943662]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/recall@5` | 0.957746 (95% CI [0.901408, 1]; n=71 clusters; observations=142) | No completed phase | 0 / — |
| `household/hybrid_runtime/returned_count@5` | 4.47436 (95% CI [4.12821, 4.76923]; n=78 clusters; observations=156) | No completed phase | 0 / — |
| `image/hybrid_runtime/f1@5` | 0.45348 (95% CI [0.437363, 0.461538]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/map@5` | 0.322813 (95% CI [0.283646, 0.35125]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/mrr@5` | 0.95 (95% CI [0.85, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/ndcg@5` | 0.69118 (95% CI [0.675482, 0.705647]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/precision@5` | 0.62 (95% CI [0.6, 0.66]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/r_precision@5` | 0.3625 (95% CI [0.3375, 0.375]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/recall@5` | 0.3625 (95% CI [0.3375, 0.375]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `image/hybrid_runtime/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/f1@5` | 0.784215 (95% CI [0.647022, 0.909091]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/map@5` | 0.695833 (95% CI [0.545833, 0.833333]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/ndcg@5` | 0.972273 (95% CI [0.916818, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/precision@5` | 0.96 (95% CI [0.88, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/r_precision@5` | 0.695833 (95% CI [0.545833, 0.833333]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/recall@5` | 0.695833 (95% CI [0.545833, 0.833333]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `scanned/hybrid_runtime/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `table/hybrid_runtime/f1@5` | 0.357143 (95% CI [0.333333, 0.404762]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/precision@5` | 0.22 (95% CI [0.2, 0.26]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `table/hybrid_runtime/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `text/hybrid_runtime/f1@5` | 0.336665 (95% CI [0.314521, 0.358809]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/hit@5` | 0.962963 (95% CI [0.91358, 1]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/map@5` | 0.905967 (95% CI [0.845473, 0.958025]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/mrr@5` | 0.909053 (95% CI [0.847325, 0.961728]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/ndcg@5` | 0.920439 (95% CI [0.866863, 0.966443]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/precision@5` | 0.207407 (95% CI [0.190123, 0.22716]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/r_precision@5` | 0.882716 (95% CI [0.808642, 0.944444]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/recall@5` | 0.962963 (95% CI [0.91358, 1]; n=81 clusters; observations=162) | No completed phase | 0 / — |
| `text/hybrid_runtime/returned_count@5` | 4.54444 (95% CI [4.25556, 4.8]; n=90 clusters; observations=180) | No completed phase | 0 / — |

### RRF sensitivity, optional reranker and robustness

Sensitivity tests use RRF k=10/30/60/100. Configured channel weights are all equal to 1, so “configured” and “equal” weighted experiments coincide by design; this is not evidence that arbitrary unequal weights are equivalent. The optional reranker is evaluated rather than assumed beneficial. All settings and K values remain in the complete CSV and raw results.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `all/hybrid_runtime/gold_modality_hit@1` | 0.92562 (95% CI [0.876033, 0.966942]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/gold_modality_hit@10` | 0.983471 (95% CI [0.958678, 1]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/gold_modality_hit@3` | 0.950413 (95% CI [0.909091, 0.983471]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/gold_modality_hit@5` | 0.983471 (95% CI [0.958678, 1]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/hybrid_runtime/modality_entropy@1` | 0 (95% CI [0, 0]; degenerate empirical interval; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/modality_entropy@10` | 0.669933 (95% CI [0.59351, 0.744876]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/modality_entropy@3` | 0.342648 (95% CI [0.267265, 0.41803]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/modality_entropy@5` | 0.669933 (95% CI [0.59351, 0.744876]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/unique_source_ratio@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/unique_source_ratio@10` | 0.555597 (95% CI [0.510821, 0.6]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/unique_source_ratio@3` | 0.659204 (95% CI [0.611878, 0.708955]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/hybrid_runtime/unique_source_ratio@5` | 0.555597 (95% CI [0.510821, 0.6]; n=134 clusters; observations=268) | No completed phase | 0 / — |
| `all/reranked_diagnostic10/mrr@5` | 0.92562 (95% CI [0.882231, 0.96281]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/reranked_diagnostic10/ndcg@5` | 0.872476 (95% CI [0.827776, 0.914175]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/reranked_diagnostic10/recall@5` | 0.799242 (95% CI [0.738809, 0.858643]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_configured_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_configured_weights/ndcg@5` | 0.8955 (95% CI [0.855756, 0.930562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_configured_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_equal_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_equal_weights/ndcg@5` | 0.8955 (95% CI [0.855756, 0.930562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_100_equal_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_configured_weights/mrr@5` | 0.938705 (95% CI [0.900138, 0.971763]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_configured_weights/ndcg@5` | 0.904775 (95% CI [0.868264, 0.937174]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_configured_weights/recall@5` | 0.840565 (95% CI [0.786493, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_equal_weights/mrr@5` | 0.938705 (95% CI [0.900138, 0.971763]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_equal_weights/ndcg@5` | 0.904775 (95% CI [0.868264, 0.937174]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_10_equal_weights/recall@5` | 0.840565 (95% CI [0.786493, 0.892562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_configured_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_configured_weights/ndcg@5` | 0.894766 (95% CI [0.855054, 0.929956]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_configured_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_equal_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_equal_weights/ndcg@5` | 0.894766 (95% CI [0.855054, 0.929956]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_30_equal_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_configured_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_configured_weights/ndcg@5` | 0.8955 (95% CI [0.855756, 0.930562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_configured_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_equal_weights/mrr@5` | 0.930854 (95% CI [0.888154, 0.968871]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_equal_weights/ndcg@5` | 0.8955 (95% CI [0.855756, 0.930562]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `all/rrf_60_equal_weights/recall@5` | 0.8323 (95% CI [0.776343, 0.886196]; n=121 clusters; observations=242) | No completed phase | 0 / — |
| `cross_modal/dense/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/dense/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/returned_count@10` | 8.2 (95% CI [4.6, 10]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/returned_count@3` | 2.6 (95% CI [1.8, 3]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/dense/returned_count@5` | 4.2 (95% CI [2.6, 5]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/fuzzy/f1@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/hit@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/map@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/map@10` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/map@3` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/map@5` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/mrr@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/mrr@10` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/mrr@3` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/mrr@5` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/ndcg@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/ndcg@10` | 0.926186 (95% CI [0.778558, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/ndcg@3` | 0.926186 (95% CI [0.778558, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/ndcg@5` | 0.926186 (95% CI [0.778558, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/precision@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/r_precision@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/r_precision@10` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/r_precision@3` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/r_precision@5` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/recall@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/returned_count@10` | 1.2 (95% CI [1, 1.6]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/returned_count@3` | 1.2 (95% CI [1, 1.6]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/fuzzy/returned_count@5` | 1.2 (95% CI [1, 1.6]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/hybrid_diagnostic10/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_diagnostic10/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/hybrid_runtime/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/returned_count@10` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_runtime/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/hybrid_text_diagnostic10/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/returned_count@10` | 8.2 (95% CI [4.6, 10]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/returned_count@3` | 2.6 (95% CI [1.8, 3]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/hybrid_text_diagnostic10/returned_count@5` | 4.2 (95% CI [2.6, 5]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/reranked_diagnostic10/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/reranked_diagnostic10/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_100_configured_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_configured_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_100_equal_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_100_equal_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_10_configured_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_configured_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_10_equal_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_10_equal_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_30_configured_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_configured_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_30_equal_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_30_equal_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_60_configured_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_configured_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/rrf_60_equal_weights/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/rrf_60_equal_weights/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/source_page_hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/text_modality_hit@5` | 0.6 (95% CI [0.2, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/visual/f1@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/hit@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/map@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/map@10` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/map@3` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/map@5` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/mrr@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/mrr@10` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/mrr@3` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/mrr@5` | 0.866667 (95% CI [0.6, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/ndcg@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/ndcg@10` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/ndcg@3` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/ndcg@5` | 0.9 (95% CI [0.7, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/precision@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/r_precision@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/r_precision@10` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/r_precision@3` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/r_precision@5` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/recall@1` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/returned_count@10` | 10 (95% CI [10, 10]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/returned_count@3` | 3 (95% CI [3, 3]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/visual/returned_count@5` | 5 (95% CI [5, 5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/empty_candidate_rate` | NOT MEASURED (n=0/0; No unanswerable questions in subset) | No completed phase | NOT MEASURED / — |
| `cross_modal/word/f1@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/f1@10` | 0.181818 (95% CI [0.181818, 0.181818]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/f1@3` | 0.5 (95% CI [0.5, 0.5]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/f1@5` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/hit@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/hit@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/hit@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/hit@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/map@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/map@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/map@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/map@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/mrr@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/mrr@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/mrr@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/mrr@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/ndcg@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/ndcg@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/ndcg@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/ndcg@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/precision@10` | 0.1 (95% CI [0.1, 0.1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/precision@3` | 0.333333 (95% CI [0.333333, 0.333333]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/precision@5` | 0.2 (95% CI [0.2, 0.2]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/r_precision@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/r_precision@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/r_precision@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/r_precision@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/recall@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/recall@10` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/recall@3` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/returned_count@1` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/returned_count@10` | 8.2 (95% CI [4.6, 10]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/returned_count@3` | 2.6 (95% CI [1.8, 3]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `cross_modal/word/returned_count@5` | 4.2 (95% CI [2.6, 5]; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `degraded_scan/hit@5` | 0.666667 (95% CI [0.333333, 1]; n=6 clusters; observations=12) | No completed phase | 0 / — |
| `degraded_scan/mrr@5` | 0.666667 (95% CI [0.333333, 1]; n=6 clusters; observations=12) | No completed phase | 0 / — |
| `degraded_scan/recall@5` | 0.388889 (95% CI [0.166667, 0.611111]; n=6 clusters; observations=12) | No completed phase | 0 / — |
| `paraphrase/independent_paraphrase_set` | NOT MEASURED (n=0/0; Frozen dataset contains typo/Hinglish variants but no separately labeled paraphrase subset; no new gold questions introduced after freeze.) | No completed phase | NOT MEASURED / — |
| `typo/pairwise_top1_consistency` | 0.904762 (CI NOT MEASURED; n/run=63/63) | No completed phase | 0 / — |
| `typo/reranked_diagnostic10/mrr@5` | 0.861842 (95% CI [0.756579, 0.953947]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/reranked_diagnostic10/ndcg@5` | 0.876933 (95% CI [0.77694, 0.961151]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/reranked_diagnostic10/recall@5` | 0.921053 (95% CI [0.815789, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_configured_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_configured_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_equal_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_equal_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_100_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_configured_weights/mrr@5` | 0.969298 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_configured_weights/ndcg@5` | 0.97713 (95% CI [0.941102, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_equal_weights/mrr@5` | 0.969298 (95% CI [0.921053, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_equal_weights/ndcg@5` | 0.97713 (95% CI [0.941102, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_10_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_configured_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_configured_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_equal_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_equal_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_30_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_configured_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_configured_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_configured_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_equal_weights/mrr@5` | 0.965789 (95% CI [0.910526, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_equal_weights/ndcg@5` | 0.974152 (95% CI [0.932169, 1]; n=38 clusters; observations=76) | No completed phase | 0 / — |
| `typo/rrf_60_equal_weights/recall@5` | 1 (95% CI [1, 1]; degenerate empirical interval; n=38 clusters; observations=76) | No completed phase | 0 / — |

### Strict cache privacy gap

Baseline sensitive-answer canary persistence: 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2). The requested zero-sensitive-content cache target is **NOT MET**. Household/user isolation is a separate check and does not remove this persistence. Private process-log leakage remains NOT MEASURED; no real private logs were inspected.

## B/C/D: generation, citations and abstention

Exact match, token F1 and ROUGE-L compare reference wording and can penalize valid longer answers. Custom E5 BERTScore is token alignment using the pinned multilingual embedding encoder, not the standard English BERTScore benchmark. Gold citation scores check authored chunk/page gold and exact canonical quotation; they are not independent per-claim faithfulness scores. Literal term coverage and answer/reference length ratio are diagnostics, not semantic correctness/completeness. Three-run consistency is a predeclared five-question sample, distinct from the two full 60-question passes.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `abstention_precision` | 0.777778 (95% CI [0.444444, 1]; n=9 clusters; observations=18) | No completed phase | 0 / — |
| `abstention_recall` | 0.7 (95% CI [0.4, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `answer_completeness_judged` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `answer_conciseness_judged` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `answer_reference_length_ratio` | 6.96399 (95% CI [5.81108, 8.20083]; n=50 clusters; observations=100) | No completed phase | 0.291682 / — |
| `answer_reference_length_ratio__chart` | 10.5578 (95% CI [7.62417, 13.5267]; n=10 clusters; observations=20) | No completed phase | 0.589256 / — |
| `answer_reference_length_ratio__image` | 6.03125 (95% CI [4.34984, 7.76281]; n=10 clusters; observations=20) | No completed phase | 0.822012 / — |
| `answer_reference_length_ratio__scanned` | 6.30536 (95% CI [3.65833, 9.37984]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `answer_reference_length_ratio__table` | 7.72 (95% CI [5.48333, 10.1418]; n=10 clusters; observations=20) | No completed phase | 0.0471405 / — |
| `answer_reference_length_ratio__text` | 4.20556 (95% CI [3.07639, 5.73889]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_authored_region_overlap_rate` | 0.773438 (95% CI [0.700521, 0.848958]; n=16 clusters; observations=32) | No completed phase | 0.0147314 / — |
| `citation_authored_region_overlap_rate__chart` | 0.755208 (95% CI [0.692708, 0.833333]; n=8 clusters; observations=16) | No completed phase | 0 / — |
| `citation_authored_region_overlap_rate__image` | 0.791667 (95% CI [0.666667, 0.916667]; n=8 clusters; observations=16) | No completed phase | 0.0294628 / — |
| `citation_authored_region_overlap_rate__scanned` | NOT MEASURED (n=0/0; No applicable observed values) | No completed phase | NOT MEASURED / — |
| `citation_authored_region_overlap_rate__table` | NOT MEASURED (n=0/0; No applicable observed values) | No completed phase | NOT MEASURED / — |
| `citation_authored_region_overlap_rate__text` | NOT MEASURED (n=0/0; No applicable observed values) | No completed phase | NOT MEASURED / — |
| `citation_browser_clickthrough_correct_page_region` | NOT MEASURED (n=60/60; This runner validates canonical citation metadata and exact quotes; no supported browser page/region click-through was executed.) | No completed phase | NOT MEASURED / — |
| `citation_canonical_page_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=48 clusters; observations=96) | No completed phase | 0 / — |
| `citation_canonical_page_rate__chart` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_canonical_page_rate__image` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_canonical_page_rate__scanned` | 1 (95% CI [1, 1]; degenerate empirical interval; n=8 clusters; observations=16) | No completed phase | 0 / — |
| `citation_canonical_page_rate__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_canonical_page_rate__text` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_claim_f1` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `citation_claim_precision` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `citation_claim_recall` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `citation_exact_quote_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=48 clusters; observations=96) | No completed phase | 0 / — |
| `citation_exact_quote_rate__chart` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_exact_quote_rate__image` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_exact_quote_rate__scanned` | 1 (95% CI [1, 1]; degenerate empirical interval; n=8 clusters; observations=16) | No completed phase | 0 / — |
| `citation_exact_quote_rate__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_exact_quote_rate__text` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_f1` | 0.615231 (95% CI [0.516877, 0.710188]; n=50 clusters; observations=100) | No completed phase | 0.00205704 / — |
| `citation_gold_f1__chart` | 0.285535 (95% CI [0.236304, 0.343728]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_f1__image` | 0.41101 (95% CI [0.308081, 0.501313]; n=10 clusters; observations=20) | No completed phase | 0.0102852 / — |
| `citation_gold_f1__scanned` | 0.43961 (95% CI [0.26362, 0.616234]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_f1__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_f1__text` | 0.94 (95% CI [0.82, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_page_recall` | 0.925 (95% CI [0.855, 0.985]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `citation_gold_page_recall__chart` | 0.95 (95% CI [0.85, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_page_recall__image` | 0.95 (95% CI [0.85, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_page_recall__scanned` | 0.8 (95% CI [0.5, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_page_recall__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_page_recall__text` | 0.925 (95% CI [0.775, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_precision` | 0.8355 (95% CI [0.754, 0.9105]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `citation_gold_precision__chart` | 0.6125 (95% CI [0.45, 0.7875]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_precision__image` | 0.925 (95% CI [0.8, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_precision__scanned` | 0.64 (95% CI [0.395, 0.8625]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_precision__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_precision__text` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_recall` | 0.56125 (95% CI [0.454167, 0.66625]; n=50 clusters; observations=100) | No completed phase | 0.00176777 / — |
| `citation_gold_recall__chart` | 0.20625 (95% CI [0.160417, 0.25625]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_recall__image` | 0.275 (95% CI [0.2, 0.34375]; n=10 clusters; observations=20) | No completed phase | 0.00883883 / — |
| `citation_gold_recall__scanned` | 0.4 (95% CI [0.216667, 0.583333]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_recall__table` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `citation_gold_recall__text` | 0.925 (95% CI [0.775, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `claim_groundedness` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `consistency_over_three_runs` | 0.8 (95% CI [0.4, 1]; n=5 clusters; observations=5) | No completed phase | NOT MEASURED / — |
| `custom_e5_bertscore_f1` | 0.826653 (95% CI [0.809117, 0.843893]; n=50 clusters; observations=100) | No completed phase | 0.0011532 / — |
| `custom_e5_bertscore_f1__chart` | 0.813962 (95% CI [0.790729, 0.837195]; n=10 clusters; observations=20) | No completed phase | 0.00445426 / — |
| `custom_e5_bertscore_f1__image` | 0.764054 (95% CI [0.729225, 0.800277]; n=10 clusters; observations=20) | No completed phase | 0.00108875 / — |
| `custom_e5_bertscore_f1__scanned` | 0.837923 (95% CI [0.786354, 0.878842]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `custom_e5_bertscore_f1__table` | 0.833488 (95% CI [0.81328, 0.849486]; n=10 clusters; observations=20) | No completed phase | 0.000222961 / — |
| `custom_e5_bertscore_f1__text` | 0.88384 (95% CI [0.863911, 0.898584]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `custom_e5_bertscore_precision` | 0.798227 (95% CI [0.782581, 0.813857]; n=50 clusters; observations=100) | No completed phase | 0.00113297 / — |
| `custom_e5_bertscore_precision__chart` | 0.786757 (95% CI [0.764551, 0.809399]; n=10 clusters; observations=20) | No completed phase | 0.00460761 / — |
| `custom_e5_bertscore_precision__image` | 0.744716 (95% CI [0.719524, 0.771161]; n=10 clusters; observations=20) | No completed phase | 0.000784041 / — |
| `custom_e5_bertscore_precision__scanned` | 0.808928 (95% CI [0.764458, 0.84727]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `custom_e5_bertscore_precision__table` | 0.795911 (95% CI [0.77829, 0.81137]; n=10 clusters; observations=20) | No completed phase | 0.000273225 / — |
| `custom_e5_bertscore_precision__text` | 0.854824 (95% CI [0.835794, 0.868643]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `custom_e5_bertscore_recall` | 0.857614 (95% CI [0.836789, 0.877218]; n=50 clusters; observations=100) | No completed phase | 0.00114225 / — |
| `custom_e5_bertscore_recall__chart` | 0.843378 (95% CI [0.817957, 0.868623]; n=10 clusters; observations=20) | No completed phase | 0.004268 / — |
| `custom_e5_bertscore_recall__image` | 0.785409 (95% CI [0.738169, 0.83382]; n=10 clusters; observations=20) | No completed phase | 0.00128475 / — |
| `custom_e5_bertscore_recall__scanned` | 0.86936 (95% CI [0.812099, 0.913684]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `custom_e5_bertscore_recall__table` | 0.874922 (95% CI [0.850708, 0.892033]; n=10 clusters; observations=20) | No completed phase | 0.000158514 / — |
| `custom_e5_bertscore_recall__text` | 0.915001 (95% CI [0.892423, 0.931936]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `embedding_semantic_similarity` | 0.846601 (95% CI [0.833498, 0.85941]; n=50 clusters; observations=100) | No completed phase | 0.00065448 / — |
| `embedding_semantic_similarity__chart` | 0.838858 (95% CI [0.818662, 0.860749]; n=10 clusters; observations=20) | No completed phase | 0.00168809 / — |
| `embedding_semantic_similarity__image` | 0.795379 (95% CI [0.771508, 0.819573]; n=10 clusters; observations=20) | No completed phase | 0.00156581 / — |
| `embedding_semantic_similarity__scanned` | 0.868357 (95% CI [0.835758, 0.896037]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `embedding_semantic_similarity__table` | 0.843445 (95% CI [0.826216, 0.859995]; n=10 clusters; observations=20) | No completed phase | 1.84941e-05 / — |
| `embedding_semantic_similarity__text` | 0.886967 (95% CI [0.876289, 0.896685]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `exact_match` | 0 (95% CI [0, 0]; degenerate empirical interval; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `exact_match__chart` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `exact_match__image` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `exact_match__scanned` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `exact_match__table` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `exact_match__text` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `false_refusal_rate` | 0.04 (95% CI [0, 0.1]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `generation_model_calls` | 56 (CI NOT MEASURED; n/run=60/60) | No completed phase | 0 / — |
| `hallucination_rate` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `negative_answer_rate` | 0.3 (95% CI [0, 0.6]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `ragas_answer_correctness` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_answer_relevancy` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_answer_similarity` | 0.846601 (95% CI [0.833498, 0.85941]; n=50 clusters; observations=100) | No completed phase | 0.00065448 / — |
| `ragas_answer_similarity__chart` | 0.838858 (95% CI [0.818662, 0.860749]; n=10 clusters; observations=20) | No completed phase | 0.00168809 / — |
| `ragas_answer_similarity__image` | 0.795379 (95% CI [0.771508, 0.819573]; n=10 clusters; observations=20) | No completed phase | 0.00156581 / — |
| `ragas_answer_similarity__scanned` | 0.868357 (95% CI [0.835758, 0.896037]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `ragas_answer_similarity__table` | 0.843445 (95% CI [0.826216, 0.859995]; n=10 clusters; observations=20) | No completed phase | 1.84924e-05 / — |
| `ragas_answer_similarity__text` | 0.886967 (95% CI [0.876289, 0.896685]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `ragas_context_entity_recall` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_context_precision` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_context_recall` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_factual_correctness` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_faithfulness` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_multimodal_faithfulness` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_multimodal_relevance` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `ragas_noise_sensitivity` | NOT MEASURED (n=60/60; No free-tier judge credential configured; lexical/reference overlap is not a substitute for independent semantic judgment.) | No completed phase | NOT MEASURED / — |
| `reference_term_coverage_diagnostic` | 0.715 (95% CI [0.59, 0.83]; n=50 clusters; observations=100) | No completed phase | 0.00707107 / — |
| `reference_term_coverage_diagnostic__chart` | 0.55 (95% CI [0.25, 0.85]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `reference_term_coverage_diagnostic__image` | 0.525 (95% CI [0.25, 0.8]; n=10 clusters; observations=20) | No completed phase | 0.0353553 / — |
| `reference_term_coverage_diagnostic__scanned` | 0.7 (95% CI [0.4, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `reference_term_coverage_diagnostic__table` | 0.95 (95% CI [0.85, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `reference_term_coverage_diagnostic__text` | 0.85 (95% CI [0.6, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `rouge_l` | 0.19465 (95% CI [0.150359, 0.243713]; n=50 clusters; observations=100) | No completed phase | 0.00305643 / — |
| `rouge_l__chart` | 0.112584 (95% CI [0.0820679, 0.145919]; n=10 clusters; observations=20) | No completed phase | 0.0064111 / — |
| `rouge_l__image` | 0.088183 (95% CI [0.0416274, 0.135443]; n=10 clusters; observations=20) | No completed phase | 0.00846995 / — |
| `rouge_l__scanned` | 0.269274 (95% CI [0.116284, 0.4463]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `rouge_l__table` | 0.203378 (95% CI [0.138591, 0.260707]; n=10 clusters; observations=20) | No completed phase | 0.000401082 / — |
| `rouge_l__text` | 0.29983 (95% CI [0.239746, 0.35492]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `three_run_pairwise_token_f1` | 0.895238 (95% CI [0.685714, 1]; n=5 clusters; observations=5) | No completed phase | NOT MEASURED / — |
| `token_f1` | 0.199764 (95% CI [0.155699, 0.248924]; n=50 clusters; observations=100) | No completed phase | 0.00307247 / — |
| `token_f1__chart` | 0.117584 (95% CI [0.0836172, 0.153976]; n=10 clusters; observations=20) | No completed phase | 0.0064111 / — |
| `token_f1__image` | 0.093183 (95% CI [0.0442114, 0.14276]; n=10 clusters; observations=20) | No completed phase | 0.00846995 / — |
| `token_f1__scanned` | 0.269274 (95% CI [0.116284, 0.4463]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `token_f1__table` | 0.21895 (95% CI [0.150634, 0.277922]; n=10 clusters; observations=20) | No completed phase | 0.000481298 / — |
| `token_f1__text` | 0.29983 (95% CI [0.239746, 0.35492]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `verification_model_calls` | 31 (CI NOT MEASURED; n/run=60/60) | No completed phase | 0 / — |

## E/H/I: household locations, freshness, cache and calibration

Uploaded-document Q/A fact presence is distinct from automatic structured entity extraction. Cache hit rate and cached-answer correctness are separate measurements. Generated-answer call savings are measured on a separate instrumented pair, not inferred from saved inventory fields. Room/zone/container and full-path denominators differ; only one container case is available. The current endpoint has no effective follow-up history support. Categorical confidence cannot be used as a numeric correctness probability for AUROC, Brier, ECE or reliability bins.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `E.aggregate_fact_presence` | 0.333333 (95% CI [0, 1]; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `E.container_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `E.delete_freshness` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `E.document_amount_fact_presence` | 1 (95% CI [1, 1]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `E.document_date_fact_presence` | 1 (95% CI [1, 1]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `E.document_identifier_fact_presence` | 1 (95% CI [1, 1]; degenerate empirical interval; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `E.document_name_extraction` | NOT MEASURED (n=0/0; Frozen household records contain no ground-truth person-name fields, and API has no automatic structured person-name extraction output.) | No completed phase | NOT MEASURED / — |
| `E.document_type_extraction` | NOT MEASURED (n=0/0; API emits MIME type and supplied filename, but has no automatic semantic document-type extraction output. No metadata value substituted.) | No completed phase | NOT MEASURED / — |
| `E.duplicate_location_handling` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `E.follow-up_fact_presence` | 0.333333 (95% CI [0, 1]; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `E.follow_up_history_support` | 0 (95% CI [0, 0]; degenerate empirical interval; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `E.full_path_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=20 clusters; observations=40) | No completed phase | 0 / — |
| `E.location_link_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=20 clusters; observations=40) | No completed phase | 0 / — |
| `E.move_freshness` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `E.room_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=20 clusters; observations=40) | No completed phase | 0 / — |
| `E.upload_index_ready_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=20 clusters; observations=40) | No completed phase | 0 / — |
| `E.upload_response_to_ready_mean_ms` | 2534.75 (95% CI [2072.11, 3096.69]; n=20 clusters; observations=40) | No completed phase | 53.4526 / — |
| `E.zone_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=20 clusters; observations=40) | No completed phase | 0 / — |
| `H.bypass_http_mean_ms` | 140.341 (95% CI [88.8584, 194.545]; n=5 clusters; observations=10) | No completed phase | 10.1492 / — |
| `H.exact_answer_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `H.exact_correct_answer_hit_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `H.exact_hit_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `H.exact_http_mean_ms` | 66.9641 (95% CI [50.7144, 83.3369]; n=5 clusters; observations=10) | No completed phase | 25.8652 / — |
| `H.exact_latency_saved_ms` | 73.3768 (CI NOT MEASURED; n/run=5/5) | No completed phase | 36.0144 / — |
| `H.generated_cache_exact_hit` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `H.generated_cache_http_ms` | 247.449 (95% CI [247.449, 247.449]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 59.8457 / — |
| `H.generated_inprocess_bypass_llm_calls` | 2 (95% CI [2, 2]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `H.generated_inprocess_cache_hit` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `H.generated_inprocess_cached_llm_calls` | 0 (95% CI [0, 0]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `H.generated_inprocess_fact_presence` | 1 (95% CI [1, 1]; degenerate empirical interval; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `H.generated_inprocess_latency_saved_ms` | 9463.87 (95% CI [9463.87, 9463.87]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 1719.44 / — |
| `H.generated_observed_latency_saved_ms` | 9423.39 (95% CI [9423.39, 9423.39]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 1426.09 / — |
| `H.generated_prime_http_ms` | 9670.84 (95% CI [9670.84, 9670.84]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 1366.24 / — |
| `H.item_move_delete_freshness` | 1 (95% CI [1, 1]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `H.llm_http_calls_saved` | 2 (95% CI [2, 2]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `H.move_delete_invalidation` | 1 (95% CI [1, 1]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `H.near_miss_false_hit_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `H.semantic_hit_rate` | 0.8 (95% CI [0.5, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `H.semantic_http_mean_ms` | 439.495 (95% CI [320.298, 557.771]; n=10 clusters; observations=20) | No completed phase | 171.91 / — |
| `H.variant_answer_accuracy` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `H.variant_correct_answer_hit_rate` | 0.8 (95% CI [0.5, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `H.variant_hit_rate` | 0.8 (95% CI [0.5, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `H.warmup_http_ms` | 156.204 (95% CI [156.204, 156.204]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 18.3764 / — |
| `I.AUROC` | NOT MEASURED (n=62/62; Application emits categorical confidence (supported/conflicting/insufficient), not a numeric correctness probability. Calibration cannot be computed honestly.) | No completed phase | NOT MEASURED / — |
| `I.Brier` | NOT MEASURED (n=62/62; Application emits categorical confidence (supported/conflicting/insufficient), not a numeric correctness probability. Calibration cannot be computed honestly.) | No completed phase | NOT MEASURED / — |
| `I.ECE` | NOT MEASURED (n=62/62; Application emits categorical confidence (supported/conflicting/insufficient), not a numeric correctness probability. Calibration cannot be computed honestly.) | No completed phase | NOT MEASURED / — |
| `I.reliability_table` | NOT MEASURED (n=62/62; Application emits categorical confidence (supported/conflicting/insufficient), not a numeric correctness probability. Calibration cannot be computed honestly.) | No completed phase | NOT MEASURED / — |

## F: ingestion, OCR, tables, visual evidence and chunking

OCR uses authored page transcripts. Literal table-cell presence and flattened row sequence are not structured table extraction or TEDS. Image labels and chart numerals are text extraction diagnostics, not chart reasoning, semantic figure detection, captions or hallucination judgment. Parser timing excludes upload, queueing, embeddings and database publication.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `chart.axis_legend_text_recall` | 1 (95% CI [1, 1]; degenerate empirical interval; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `chart.numeric_label_text_recall` | 0.75 (95% CI [0.5, 1]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `chart.structured_reading_accuracy` | NOT MEASURED (n=0/0; Ingestion does not emit bar-to-value/month associations. End-to-end chart QA is evaluated by the generation specialist.) | No completed phase | NOT MEASURED / — |
| `chunking.chart.content_characters_max` | 88 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.content_characters_mean` | 14.4286 (95% CI [8.83929, 20.9826]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.content_characters_min` | 1 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.content_characters_p50` | 5 (95% CI [3, 5]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.content_characters_p95` | 82 (95% CI [36.5, 88]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.indexed_characters_max` | 104 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.indexed_characters_mean` | 30.4286 (95% CI [24.8393, 36.9826]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.indexed_characters_min` | 17 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.indexed_characters_p50` | 21 (95% CI [19, 21]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.indexed_characters_p95` | 98 (95% CI [52.5, 104]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.literal_evidence_all_terms_rate` | 0.4 (95% CI [0.1, 0.7]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.chart.literal_evidence_single_chunk_rate` | 0.4 (95% CI [0.1, 0.7]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.chart.literal_evidence_term_coverage` | 0.5 (95% CI [0.25, 0.75]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.chart.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.reference_evidence_spread_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.chart.whitespace_words_max` | 21 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.whitespace_words_mean` | 3.39286 (95% CI [2.17857, 4.875]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.whitespace_words_min` | 1 (CI NOT MEASURED; n/run=56/56) | No completed phase | 0 / — |
| `chunking.chart.whitespace_words_p50` | 1 (95% CI [1, 2]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.chart.whitespace_words_p95` | 20.25 (95% CI [5.5, 21]; n=56 clusters; observations=112) | No completed phase | 0 / — |
| `chunking.figure_label_caption_single_chunk_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.image.content_characters_max` | 83 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.content_characters_mean` | 24.625 (95% CI [16.3125, 34.0008]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.content_characters_min` | 3 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.content_characters_p50` | 17.5 (95% CI [4, 32]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.content_characters_p95` | 83 (95% CI [36, 83]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.indexed_characters_max` | 99 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.indexed_characters_mean` | 40.625 (95% CI [32.3125, 50.0008]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.indexed_characters_min` | 19 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.indexed_characters_p50` | 33.5 (95% CI [20, 48]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.indexed_characters_p95` | 99 (95% CI [52, 99]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.literal_evidence_all_terms_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.image.literal_evidence_single_chunk_rate` | 0.9 (95% CI [0.7, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.image.literal_evidence_term_coverage` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.image.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.reference_evidence_spread_rate` | 0.1 (95% CI [0, 0.3]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.image.whitespace_words_max` | 15 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.whitespace_words_mean` | 4.375 (95% CI [2.90625, 6.03125]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.whitespace_words_min` | 1 (CI NOT MEASURED; n/run=32/32) | No completed phase | 0 / — |
| `chunking.image.whitespace_words_p50` | 3 (95% CI [1, 5]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.image.whitespace_words_p95` | 15 (95% CI [6, 15]; n=32 clusters; observations=64) | No completed phase | 0 / — |
| `chunking.overall.content_characters_max` | 257 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.content_characters_mean` | 36.5083 (95% CI [26.9329, 47.025]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.content_characters_min` | 1 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.content_characters_p50` | 16 (95% CI [5, 27]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.content_characters_p95` | 148 (95% CI [90.95, 257]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.indexed_characters_max` | 273 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.indexed_characters_mean` | 52.5083 (95% CI [42.9329, 63.025]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.indexed_characters_min` | 17 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.indexed_characters_p50` | 32 (95% CI [21, 43]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.indexed_characters_p95` | 164 (95% CI [106.95, 273]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.literal_evidence_all_terms_rate` | 0.88 (95% CI [0.78, 0.96]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `chunking.overall.literal_evidence_single_chunk_rate` | 0.78 (95% CI [0.66, 0.8805]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `chunking.overall.literal_evidence_term_coverage` | 0.9 (95% CI [0.82, 0.97]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `chunking.overall.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.reference_evidence_spread_rate` | 0.1 (95% CI [0.02, 0.18]; n=50 clusters; observations=100) | No completed phase | 0 / — |
| `chunking.overall.whitespace_words_max` | 44 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.whitespace_words_mean` | 6.68333 (95% CI [5.00813, 8.53333]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.whitespace_words_min` | 1 (CI NOT MEASURED; n/run=120/120) | No completed phase | 0 / — |
| `chunking.overall.whitespace_words_p50` | 3 (95% CI [2, 5]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.overall.whitespace_words_p95` | 28 (95% CI [21.1, 44]; n=120 clusters; observations=240) | No completed phase | 0 / — |
| `chunking.scanned.content_characters_max` | 148 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.content_characters_mean` | 48.6667 (95% CI [32.7073, 68.4177]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.content_characters_min` | 21 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.content_characters_p50` | 31.5 (95% CI [22, 38]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.content_characters_p95` | 148 (95% CI [38, 148]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.indexed_characters_max` | 164 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.indexed_characters_mean` | 64.6667 (95% CI [48.7073, 84.4177]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.indexed_characters_min` | 37 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.indexed_characters_p50` | 47.5 (95% CI [38, 54]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.indexed_characters_p95` | 164 (95% CI [54, 164]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.literal_evidence_all_terms_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.scanned.literal_evidence_single_chunk_rate` | 0.9 (95% CI [0.7, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.scanned.literal_evidence_term_coverage` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.scanned.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.reference_evidence_spread_rate` | 0.1 (95% CI [0, 0.3]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.scanned.whitespace_words_max` | 23 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.whitespace_words_mean` | 7.66667 (95% CI [5.16667, 10.7083]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.whitespace_words_min` | 3 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `chunking.scanned.whitespace_words_p50` | 5.5 (95% CI [3, 6]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.scanned.whitespace_words_p95` | 23 (95% CI [6, 23]; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `chunking.semantic_answer_completeness` | NOT MEASURED (n=0/0; Literal evidence diagnostics are not semantic completeness; no external judge key is configured.) | No completed phase | NOT MEASURED / — |
| `chunking.table.content_characters_max` | 148 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.content_characters_mean` | 147.25 (95% CI [147, 147.75]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.content_characters_min` | 147 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.content_characters_p50` | 147 (95% CI [147, 148]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.content_characters_p95` | 147.85 (95% CI [147, 148]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.indexed_characters_max` | 164 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.indexed_characters_mean` | 163.25 (95% CI [163, 163.75]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.indexed_characters_min` | 163 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.indexed_characters_p50` | 163 (95% CI [163, 164]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.indexed_characters_p95` | 163.85 (95% CI [163, 164]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.literal_evidence_all_terms_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.table.literal_evidence_single_chunk_rate` | 0.9 (95% CI [0.7, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.table.literal_evidence_term_coverage` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.table.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.reference_evidence_spread_rate` | 0.1 (95% CI [0, 0.3]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.table.whitespace_words_max` | 28 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.whitespace_words_mean` | 28 (95% CI [28, 28]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.whitespace_words_min` | 28 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.table.whitespace_words_p50` | 28 (95% CI [28, 28]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table.whitespace_words_p95` | 28 (95% CI [28, 28]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.table_split_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.content_characters_max` | 257 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.content_characters_mean` | 257 (95% CI [257, 257]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.content_characters_min` | 257 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.content_characters_p50` | 257 (95% CI [257, 257]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.content_characters_p95` | 257 (95% CI [257, 257]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.indexed_characters_max` | 273 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.indexed_characters_mean` | 273 (95% CI [273, 273]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.indexed_characters_min` | 273 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.indexed_characters_p50` | 273 (95% CI [273, 273]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.indexed_characters_p95` | 273 (95% CI [273, 273]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.literal_evidence_all_terms_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.text.literal_evidence_single_chunk_rate` | 0.8 (95% CI [0.5, 1]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.text.literal_evidence_term_coverage` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.text.location_prefix_and_metadata_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.reference_evidence_spread_rate` | 0.2 (95% CI [0, 0.5]; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `chunking.text.whitespace_words_max` | 44 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.whitespace_words_mean` | 44 (95% CI [44, 44]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.whitespace_words_min` | 44 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `chunking.text.whitespace_words_p50` | 44 (95% CI [44, 44]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `chunking.text.whitespace_words_p95` | 44 (95% CI [44, 44]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `figure.detection_recall` | NOT MEASURED (n=0/0; Production parser has raster-region OCR and page previews but no figure-region detector output. Preview retention is measured separately.) | No completed phase | NOT MEASURED / — |
| `figure.page_preview_retention_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=8 clusters; observations=16) | No completed phase | 0 / — |
| `image.caption_quality` | NOT MEASURED (n=0/0; Ingestion does not generate semantic captions; no free-tier external judge credentials are configured.) | No completed phase | NOT MEASURED / — |
| `image.hallucinated_content_rate` | NOT MEASURED (n=0/0; Ingestion emits OCR text and visual anchors, not generated descriptions. Semantic unsupported-content judging requires an unavailable external judge; OCR substitution errors are measured as CER/WER.) | No completed phase | NOT MEASURED / — |
| `image.literal_label_recall` | 1 (95% CI [1, 1]; degenerate empirical interval; n=24 clusters; observations=48) | No completed phase | 0 / — |
| `ingestion.actual_llm_calls` | 0 (CI NOT MEASURED; n/run=5/5) | No completed phase | 0 / — |
| `ingestion.actual_ocr_invocations` | 24 (CI NOT MEASURED; n/run=24/24) | No completed phase | 0 / — |
| `ingestion.chart.parser_seconds_per_page_mean` | 0.394499 (95% CI [0.362645, 0.426354]; n=4 clusters; observations=8) | No completed phase | 0.0584245 / — |
| `ingestion.chart.parser_seconds_per_page_p50` | 0.392579 (95% CI [0.349926, 0.442914]; n=4 clusters; observations=8) | No completed phase | 0.0558363 / — |
| `ingestion.chart.parser_seconds_per_page_p95` | 0.438527 (95% CI [0.375365, 0.442914]; n=4 clusters; observations=8) | No completed phase | 0.113091 / — |
| `ingestion.document_success_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=5 clusters; observations=10) | No completed phase | 0 / — |
| `ingestion.embedding_and_database_seconds_per_page` | NOT MEASURED (n=0/0; This specialist measures the actual parser directly; queue, embedding and database stage timings are outside this instrumentation.) | No completed phase | NOT MEASURED / — |
| `ingestion.image.parser_seconds_per_page_mean` | 0.348249 (95% CI [0.313583, 0.411865]; n=4 clusters; observations=8) | No completed phase | 0.000788549 / — |
| `ingestion.image.parser_seconds_per_page_p50` | 0.319311 (95% CI [0.310837, 0.443561]; n=4 clusters; observations=8) | No completed phase | 0.0121009 / — |
| `ingestion.image.parser_seconds_per_page_p95` | 0.425406 (95% CI [0.316799, 0.443561]; n=4 clusters; observations=8) | No completed phase | 0.0236196 / — |
| `ingestion.overall.parser_seconds_per_page_mean` | 0.234306 (95% CI [0.15814, 0.30966]; n=20 clusters; observations=40) | No completed phase | 0.0139534 / — |
| `ingestion.overall.parser_seconds_per_page_p50` | 0.319311 (95% CI [0.0230197, 0.363106]; n=20 clusters; observations=40) | No completed phase | 0.0121009 / — |
| `ingestion.overall.parser_seconds_per_page_p95` | 0.460223 (95% CI [0.374111, 0.495632]; n=20 clusters; observations=40) | No completed phase | 0.0183464 / — |
| `ingestion.scanned.parser_seconds_per_page_mean` | 0.381327 (95% CI [0.35519, 0.424384]; n=4 clusters; observations=8) | No completed phase | 0.00800941 / — |
| `ingestion.scanned.parser_seconds_per_page_p50` | 0.364368 (95% CI [0.35064, 0.445931]; n=4 clusters; observations=8) | No completed phase | 0.0161683 / — |
| `ingestion.scanned.parser_seconds_per_page_p95` | 0.434591 (95% CI [0.359741, 0.445931]; n=4 clusters; observations=8) | No completed phase | 0.00289917 / — |
| `ingestion.table.parser_seconds_per_page_mean` | 0.0223618 (95% CI [0.0218354, 0.0231571]; n=4 clusters; observations=8) | No completed phase | 0.000330447 / — |
| `ingestion.table.parser_seconds_per_page_p50` | 0.0221614 (95% CI [0.021768, 0.0235753]; n=4 clusters; observations=8) | No completed phase | 0.000403169 / — |
| `ingestion.table.parser_seconds_per_page_p95` | 0.0234086 (95% CI [0.0220889, 0.0235753]; n=4 clusters; observations=8) | No completed phase | 5.45824e-05 / — |
| `ingestion.text.parser_seconds_per_page_mean` | 0.0250925 (95% CI [0.0216247, 0.0315476]; n=4 clusters; observations=8) | No completed phase | 0.00221394 / — |
| `ingestion.text.parser_seconds_per_page_p50` | 0.0219822 (95% CI [0.0215797, 0.0348402]; n=4 clusters; observations=8) | No completed phase | 0.000458868 / — |
| `ingestion.text.parser_seconds_per_page_p95` | 0.0329562 (95% CI [0.0216821, 0.0348402]; n=4 clusters; observations=8) | No completed phase | 0.00649554 / — |
| `native_text.cer_macro` | 0 (95% CI [0, 0]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `native_text.cer_micro` | 0 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `native_text.wer_macro` | 0 (95% CI [0, 0]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `native_text.wer_micro` | 0 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `ocr.scanned.cer_macro` | 0.00337838 (95% CI [0, 0.0101351]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `ocr.scanned.cer_micro` | 0.00337838 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `ocr.scanned.wer_macro` | 0.0217391 (95% CI [0, 0.0652174]; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `ocr.scanned.wer_micro` | 0.0217391 (CI NOT MEASURED; n/run=4/4) | No completed phase | 0 / — |
| `table.cell_accuracy` | NOT MEASURED (n=0/0; Production PDF parser emits flat text chunks, not aligned table cells; cell accuracy would require inventing row/column reconstruction.) | No completed phase | NOT MEASURED / — |
| `table.cell_text_recall` | 1 (95% CI [1, 1]; degenerate empirical interval; n=48 clusters; observations=96) | No completed phase | 0 / — |
| `table.row_major_text_sequence_preserved_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `table.structure_teds` | NOT MEASURED (n=0/0; No structured HTML/table tree is emitted by the production PDF parser.) | No completed phase | NOT MEASURED / — |
| `table.structured_output_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |

## J/K: isolation, injection resistance and system measurements

Disposable authenticated accounts are used; no real household documents are evaluated. Authorized query/answer content intentionally persists in a household-and-user-scoped cache; this is not a claim of zero sensitive content in cache. Process logs containing possible private activity were not read. Small concurrent saved-fact probes do not establish full multimodal generation capacity. Local inference has no per-token invoice, but total hardware/energy cost was not measured. Shared-machine model contention and lock waiting are distinguished where instrumented; before/after latency differences are observational, not causal speed claims.

| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |
| --- | --- | --- | --- |
| `cost_usd_per_query` | NOT MEASURED (n=0/0; Self-hosted model has no per-token invoice. Electricity/hardware amortization and deployment prices were not instrumented; zero API billing is not zero total cost.) | No completed phase | NOT MEASURED / — |
| `full_rag_concurrency_capacity` | NOT MEASURED (n=0/0; Concurrent sample measures saved inventory field lookup only. Shared model lock serializes actual generation to protect this 16 GB development host; cannot infer production generation concurrency.) | No completed phase | NOT MEASURED / — |
| `live_recorded_fact_concurrent_failure_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=4 clusters; observations=8) | No completed phase | 0 / — |
| `live_recorded_fact_concurrent_p50_ms` | 48.3874 (95% CI [24.8048, 50.1182]; n=4 clusters; observations=8) | No completed phase | 10.0206 / — |
| `live_recorded_fact_concurrent_p95_ms` | 50.7579 (95% CI [45.7438, 50.9332]; n=4 clusters; observations=8) | No completed phase | 10.1415 / — |
| `live_recorded_fact_concurrent_throughput_rps` | 79.4872 (CI NOT MEASURED; n/run=4/4) | No completed phase | 15.6761 / — |
| `live_recorded_fact_sequential_failure_rate` | 0 (95% CI [0, 0]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `live_recorded_fact_sequential_p50_ms` | 22.5369 (95% CI [21.9688, 23.1049]; n=2 clusters; observations=4) | No completed phase | 7.17084 / — |
| `live_recorded_fact_sequential_p95_ms` | 23.0678 (95% CI [21.9688, 23.1049]; n=2 clusters; observations=4) | No completed phase | 7.89383 / — |
| `parse_text_2097152_bytes_seconds` | 0.0464653 (CI NOT MEASURED; n/run=1/1) | No completed phase | 0.000203617 / — |
| `parse_text_262144_bytes_seconds` | 0.00575183 (CI NOT MEASURED; n/run=1/1) | No completed phase | 0.000315723 / — |
| `parse_text_4096_bytes_seconds` | 0.0011161 (CI NOT MEASURED; n/run=1/1) | No completed phase | 0.000587282 / — |
| `pdf_all_generation_seconds_p50` | 89.8371 (95% CI [73.4047, 106.947]; n=60 clusters; observations=120) | No completed phase | 24.5541 / — |
| `pdf_all_generation_seconds_p95` | 179.365 (95% CI [148.185, 191.538]; n=60 clusters; observations=120) | No completed phase | 22.4058 / — |
| `pdf_all_mean_actual_new_model_calls` | 1.45 (95% CI [1.3, 1.6]; n=60 clusters; observations=120) | No completed phase | 0 / — |
| `pdf_all_mean_completion_tokens` | 361.367 (95% CI [311.243, 410.295]; n=56 clusters; observations=111) | No completed phase | 2.38717 / — |
| `pdf_all_mean_model_calls` | 1.45 (95% CI [1.3, 1.6]; n=60 clusters; observations=120) | No completed phase | 0 / — |
| `pdf_all_mean_prompt_tokens` | 12420 (95% CI [11361.7, 13508.7]; n=56 clusters; observations=111) | No completed phase | 109.277 / — |
| `pdf_all_model_embedding_seconds_p50` | 0.3215 (95% CI [0.299514, 0.354379]; n=60 clusters; observations=120) | No completed phase | 0.0391423 / — |
| `pdf_all_model_embedding_seconds_p95` | 0.988149 (95% CI [0.610006, 2.67541]; n=60 clusters; observations=120) | No completed phase | 0.286697 / — |
| `pdf_all_model_generation_seconds_p50` | 77.1864 (95% CI [68.8046, 84.1225]; n=56 clusters; observations=112) | No completed phase | 8.24899 / — |
| `pdf_all_model_generation_seconds_p95` | 115.856 (95% CI [106.783, 124.35]; n=56 clusters; observations=112) | No completed phase | 13.9816 / — |
| `pdf_all_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_all_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_all_model_verification_seconds_p50` | 25.442 (95% CI [18.102, 35.7845]; n=31 clusters; observations=62) | No completed phase | 1.36463 / — |
| `pdf_all_model_verification_seconds_p95` | 72.8954 (95% CI [58.2561, 78.5023]; n=31 clusters; observations=62) | No completed phase | 8.46019 / — |
| `pdf_all_retrieval_seconds_p50` | 1.33559 (95% CI [1.27064, 1.40237]; n=60 clusters; observations=120) | No completed phase | 0.0520009 / — |
| `pdf_all_retrieval_seconds_p95` | 4.59082 (95% CI [2.50271, 6.19212]; n=60 clusters; observations=120) | No completed phase | 3.14373 / — |
| `pdf_all_total_seconds_p50` | 90.7399 (95% CI [74.8842, 108.954]; n=60 clusters; observations=120) | No completed phase | 24.8932 / — |
| `pdf_all_total_seconds_p95` | 180.663 (95% CI [150.885, 192.576]; n=60 clusters; observations=120) | No completed phase | 22.4499 / — |
| `pdf_chart_generation_seconds_p50` | 95.61 (95% CI [73.8461, 171.177]; n=12 clusters; observations=24) | No completed phase | 17.1492 / — |
| `pdf_chart_generation_seconds_p95` | 186.491 (95% CI [160.932, 188.457]; n=12 clusters; observations=24) | No completed phase | 13.8917 / — |
| `pdf_chart_mean_actual_new_model_calls` | 1.41667 (95% CI [1, 1.75]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_chart_mean_completion_tokens` | 467.318 (95% CI [355.314, 550.91]; n=11 clusters; observations=22) | No completed phase | 0.449977 / — |
| `pdf_chart_mean_model_calls` | 1.41667 (95% CI [1, 1.75]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_chart_mean_prompt_tokens` | 14760.5 (95% CI [11448.2, 18032.7]; n=11 clusters; observations=22) | No completed phase | 530.202 / — |
| `pdf_chart_model_embedding_seconds_p50` | 0.358569 (95% CI [0.332588, 0.427352]; n=12 clusters; observations=24) | No completed phase | 0.00233232 / — |
| `pdf_chart_model_embedding_seconds_p95` | 1.14333 (95% CI [0.408338, 1.88125]; n=12 clusters; observations=24) | No completed phase | 1.03866 / — |
| `pdf_chart_model_generation_seconds_p50` | 81.2833 (95% CI [72.0352, 100.109]; n=11 clusters; observations=22) | No completed phase | 4.73376 / — |
| `pdf_chart_model_generation_seconds_p95` | 112.753 (95% CI [92.3743, 115.74]; n=11 clusters; observations=22) | No completed phase | 11.8313 / — |
| `pdf_chart_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_chart_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_chart_model_verification_seconds_p50` | 70.4588 (95% CI [49.2223, 74.1801]; n=6 clusters; observations=12) | No completed phase | 10.4423 / — |
| `pdf_chart_model_verification_seconds_p95` | 79.1001 (95% CI [72.4501, 80.8953]; n=6 clusters; observations=12) | No completed phase | 11.8568 / — |
| `pdf_chart_retrieval_seconds_p50` | 1.3129 (95% CI [1.25744, 1.47663]; n=12 clusters; observations=24) | No completed phase | 0.0199089 / — |
| `pdf_chart_retrieval_seconds_p95` | 2.51895 (95% CI [1.49336, 3.52326]; n=12 clusters; observations=24) | No completed phase | 1.54666 / — |
| `pdf_chart_total_seconds_p50` | 96.8717 (95% CI [75.1804, 172.412]; n=12 clusters; observations=24) | No completed phase | 17.0862 / — |
| `pdf_chart_total_seconds_p95` | 188.952 (95% CI [163.233, 191.884]; n=12 clusters; observations=24) | No completed phase | 12.2634 / — |
| `pdf_image_generation_seconds_p50` | 64.0572 (95% CI [35.4052, 96.0288]; n=12 clusters; observations=24) | No completed phase | 21.7982 / — |
| `pdf_image_generation_seconds_p95` | 115.467 (95% CI [87.2186, 134.012]; n=12 clusters; observations=24) | No completed phase | 54.9187 / — |
| `pdf_image_mean_actual_new_model_calls` | 1.08333 (95% CI [0.75, 1.41667]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_image_mean_completion_tokens` | 337.567 (95% CI [258.149, 422.056]; n=10 clusters; observations=19) | No completed phase | 11.6437 / — |
| `pdf_image_mean_model_calls` | 1.08333 (95% CI [0.75, 1.41667]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_image_mean_prompt_tokens` | 8651.54 (95% CI [7700.81, 9620.55]; n=10 clusters; observations=19) | No completed phase | 255.486 / — |
| `pdf_image_model_embedding_seconds_p50` | 0.392248 (95% CI [0.315764, 0.786245]; n=12 clusters; observations=24) | No completed phase | 0.115939 / — |
| `pdf_image_model_embedding_seconds_p95` | 1.34438 (95% CI [0.812922, 1.44209]; n=12 clusters; observations=24) | No completed phase | 1.08554 / — |
| `pdf_image_model_generation_seconds_p50` | 64.8497 (95% CI [51.2564, 88.2899]; n=10 clusters; observations=20) | No completed phase | 20.2149 / — |
| `pdf_image_model_generation_seconds_p95` | 106.511 (95% CI [76.7132, 114.295]; n=10 clusters; observations=20) | No completed phase | 44.5905 / — |
| `pdf_image_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_image_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_image_model_verification_seconds_p50` | 20.6402 (95% CI [11.4028, 27.6752]; n=3 clusters; observations=6) | No completed phase | 5.42605 / — |
| `pdf_image_model_verification_seconds_p95` | 28.7486 (95% CI [11.4028, 29.4521]; n=3 clusters; observations=6) | No completed phase | 11.8672 / — |
| `pdf_image_retrieval_seconds_p50` | 1.84905 (95% CI [1.27585, 3.84987]; n=12 clusters; observations=24) | No completed phase | 0.939903 / — |
| `pdf_image_retrieval_seconds_p95` | 5.08163 (95% CI [3.56253, 5.53505]; n=12 clusters; observations=24) | No completed phase | 4.88604 / — |
| `pdf_image_total_seconds_p50` | 66.0306 (95% CI [39.4978, 98.9443]; n=12 clusters; observations=24) | No completed phase | 23.2721 / — |
| `pdf_image_total_seconds_p95` | 118.224 (95% CI [88.7945, 135.729]; n=12 clusters; observations=24) | No completed phase | 56.7559 / — |
| `pdf_scanned_generation_seconds_p50` | 71.8445 (95% CI [41.3029, 120.701]; n=12 clusters; observations=24) | No completed phase | 1.59036 / — |
| `pdf_scanned_generation_seconds_p95` | 164.301 (95% CI [111.88, 196.54]; n=12 clusters; observations=24) | No completed phase | 15.937 / — |
| `pdf_scanned_mean_actual_new_model_calls` | 1.25 (95% CI [0.916667, 1.58333]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_scanned_mean_completion_tokens` | 446.455 (95% CI [311, 581.366]; n=11 clusters; observations=22) | No completed phase | 0 / — |
| `pdf_scanned_mean_model_calls` | 1.25 (95% CI [0.916667, 1.58333]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_scanned_mean_prompt_tokens` | 10758.8 (95% CI [8208.35, 13675.8]; n=11 clusters; observations=22) | No completed phase | 0 / — |
| `pdf_scanned_model_embedding_seconds_p50` | 0.303389 (95% CI [0.272399, 0.333498]; n=12 clusters; observations=24) | No completed phase | 0.0296134 / — |
| `pdf_scanned_model_embedding_seconds_p95` | 0.462162 (95% CI [0.335159, 0.493285]; n=12 clusters; observations=24) | No completed phase | 0.0749485 / — |
| `pdf_scanned_model_generation_seconds_p50` | 70.34 (95% CI [47.185, 81.0949]; n=11 clusters; observations=22) | No completed phase | 3.42011 / — |
| `pdf_scanned_model_generation_seconds_p95` | 121.415 (95% CI [77.1254, 124.68]; n=11 clusters; observations=22) | No completed phase | 11.468 / — |
| `pdf_scanned_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_scanned_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_scanned_model_verification_seconds_p50` | 51.7474 (95% CI [41.7833, 72.0427]; n=4 clusters; observations=8) | No completed phase | 4.45003 / — |
| `pdf_scanned_model_verification_seconds_p95` | 69.763 (95% CI [46.6505, 72.0427]; n=4 clusters; observations=8) | No completed phase | 8.03075 / — |
| `pdf_scanned_retrieval_seconds_p50` | 1.20434 (95% CI [1.1256, 1.35939]; n=12 clusters; observations=24) | No completed phase | 0.0207423 / — |
| `pdf_scanned_retrieval_seconds_p95` | 1.9003 (95% CI [1.39107, 2.20849]; n=12 clusters; observations=24) | No completed phase | 0.614734 / — |
| `pdf_scanned_total_seconds_p50` | 73.2793 (95% CI [42.5377, 121.584]; n=12 clusters; observations=24) | No completed phase | 2.59433 / — |
| `pdf_scanned_total_seconds_p95` | 165.509 (95% CI [113.18, 197.85]; n=12 clusters; observations=24) | No completed phase | 15.9777 / — |
| `pdf_table_generation_seconds_p50` | 91.3661 (95% CI [44.6953, 119.23]; n=12 clusters; observations=24) | No completed phase | 11.6744 / — |
| `pdf_table_generation_seconds_p95` | 131.991 (95% CI [115.339, 142.028]; n=12 clusters; observations=24) | No completed phase | 12.1636 / — |
| `pdf_table_mean_actual_new_model_calls` | 1.75 (95% CI [1.5, 2]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_table_mean_completion_tokens` | 335.292 (95% CI [266.499, 422.462]; n=12 clusters; observations=24) | No completed phase | 0.412479 / — |
| `pdf_table_mean_model_calls` | 1.75 (95% CI [1.5, 2]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_table_mean_prompt_tokens` | 13532.1 (95% CI [12462.5, 14568.3]; n=12 clusters; observations=24) | No completed phase | 0.412479 / — |
| `pdf_table_model_embedding_seconds_p50` | 0.280534 (95% CI [0.20808, 0.358755]; n=12 clusters; observations=24) | No completed phase | 0.251676 / — |
| `pdf_table_model_embedding_seconds_p95` | 0.578825 (95% CI [0.367762, 0.643375]; n=12 clusters; observations=24) | No completed phase | 0.318111 / — |
| `pdf_table_model_generation_seconds_p50` | 74.9449 (95% CI [42.5253, 93.6473]; n=12 clusters; observations=24) | No completed phase | 0.709941 / — |
| `pdf_table_model_generation_seconds_p95` | 105.942 (95% CI [92.0298, 111.007]; n=12 clusters; observations=24) | No completed phase | 9.44069 / — |
| `pdf_table_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_table_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_table_model_verification_seconds_p50` | 17.8506 (95% CI [2.11393, 27.9755]; n=9 clusters; observations=18) | No completed phase | 0.235096 / — |
| `pdf_table_model_verification_seconds_p95` | 30.8592 (95% CI [21.8661, 31.4835]; n=9 clusters; observations=18) | No completed phase | 1.37562 / — |
| `pdf_table_retrieval_seconds_p50` | 1.30874 (95% CI [1.18514, 1.44386]; n=12 clusters; observations=24) | No completed phase | 0.240961 / — |
| `pdf_table_retrieval_seconds_p95` | 1.72038 (95% CI [1.48342, 1.86775]; n=12 clusters; observations=24) | No completed phase | 0.478212 / — |
| `pdf_table_total_seconds_p50` | 92.7183 (95% CI [46.0929, 120.455]; n=12 clusters; observations=24) | No completed phase | 11.4355 / — |
| `pdf_table_total_seconds_p95` | 133.193 (95% CI [116.758, 143.768]; n=12 clusters; observations=24) | No completed phase | 11.4221 / — |
| `pdf_text_generation_seconds_p50` | 113.784 (95% CI [87.3222, 130.091]; n=12 clusters; observations=24) | No completed phase | 26.2006 / — |
| `pdf_text_generation_seconds_p95` | 152.012 (95% CI [130.019, 163.112]; n=12 clusters; observations=24) | No completed phase | 43.7524 / — |
| `pdf_text_mean_actual_new_model_calls` | 1.75 (95% CI [1.5, 2]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_text_mean_completion_tokens` | 230.75 (95% CI [150.917, 336.335]; n=12 clusters; observations=24) | No completed phase | 18.8562 / — |
| `pdf_text_mean_model_calls` | 1.75 (95% CI [1.5, 2]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_text_mean_prompt_tokens` | 13657.8 (95% CI [12611.2, 14637.5]; n=12 clusters; observations=24) | No completed phase | 0 / — |
| `pdf_text_model_embedding_seconds_p50` | 0.318519 (95% CI [0.266614, 0.446601]; n=12 clusters; observations=24) | No completed phase | 0.105562 / — |
| `pdf_text_model_embedding_seconds_p95` | 1.44536 (95% CI [0.546513, 2.38662]; n=12 clusters; observations=24) | No completed phase | 1.21092 / — |
| `pdf_text_model_generation_seconds_p50` | 83.6416 (95% CI [67.0836, 94.6738]; n=12 clusters; observations=24) | No completed phase | 10.1848 / — |
| `pdf_text_model_generation_seconds_p95` | 104.024 (95% CI [95.5809, 107.725]; n=12 clusters; observations=24) | No completed phase | 3.55861 / — |
| `pdf_text_model_reranking_seconds_p50` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_text_model_reranking_seconds_p95` | NOT MEASURED (n=0/0; No recorded timed model calls observed) | No completed phase | NOT MEASURED / — |
| `pdf_text_model_verification_seconds_p50` | 17.4428 (95% CI [3.47627, 25.8506]; n=9 clusters; observations=18) | No completed phase | 1.05274 / — |
| `pdf_text_model_verification_seconds_p95` | 32.651 (95% CI [21.3633, 35.8806]; n=9 clusters; observations=18) | No completed phase | 2.77705 / — |
| `pdf_text_retrieval_seconds_p50` | 1.51216 (95% CI [1.2075, 2.0258]; n=12 clusters; observations=24) | No completed phase | 0.0468064 / — |
| `pdf_text_retrieval_seconds_p95` | 4.82941 (95% CI [2.34742, 5.97337]; n=12 clusters; observations=24) | No completed phase | 1.83871 / — |
| `pdf_text_total_seconds_p50` | 117.55 (95% CI [89.4145, 131.487]; n=12 clusters; observations=24) | No completed phase | 26.3275 / — |
| `pdf_text_total_seconds_p95` | 154.468 (95% CI [131.125, 164.334]; n=12 clusters; observations=24) | No completed phase | 45.0915 / — |
| `pdf_timeout_rate` | NOT MEASURED (n=0/0; Generation raw stage rows do not distinguish timeout, parse failure and abstention. No invented classification.) | No completed phase | NOT MEASURED / — |
| `prompt_injection_answer_fact_rate` | 0.666667 (95% CI [0, 1]; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `prompt_injection_http_safety_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=3 clusters; observations=6) | No completed phase | 0 / — |
| `prompt_injection_resistance_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=2 clusters; observations=4) | No completed phase | 0 / — |
| `publication_sensitive_value_leak_files` | 0 (CI NOT MEASURED; n/run=177/177) | No completed phase | 0 / — |
| `security_isolation_pass_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=10 clusters; observations=20) | No completed phase | 0 / — |
| `sensitive_answer_cache_persistence_rate` | 1 (95% CI [1, 1]; degenerate empirical interval; n=1 clusters; observations=2) | No completed phase | 0 / — |
| `shared_log_sensitive_canary_leak_rate` | NOT MEASURED (n=0/0; Actual process logs may contain private user activity and were deliberately not read. Source logsites inspected separately; that is not a measured log-leak test.) | No completed phase | NOT MEASURED / — |
| `three_d_active_render_fps` | NOT MEASURED (n=0/0; No renderer instrumentation or isolated authenticated disposable GPU browser measurement in this runner. Display requestAnimationFrame rate is not scene rendering FPS.) | No completed phase | NOT MEASURED / — |
| `three_d_view_ready_seconds` | NOT MEASURED (n=0/0; No isolated disposable browser navigation measurement executed.) | No completed phase | NOT MEASURED / — |

## Limitations and interpretation

- All documents, identifiers, names and account fixtures are synthetic. This benchmark does not establish accuracy for private identity cards, multilingual handwriting, arbitrary spreadsheets or unseen household layouts.
- Related typo variants and questions from the same small document set limit generalization. The bootstrap clusters repeated runs by question ID; it does not turn the corpus into a representative population sample or account for every higher-level document dependency.
- With no independent free-tier judge, faithfulness, semantic answer correctness, claim grounding, multimodal judgment and hallucination rates remain NOT MEASURED. A matching number or an exact source quote does not prove a full answer is correct.
- Numeric trust probabilities, structured table output, dedicated semantic figure detection and image captioning are absent or unmeasured capabilities as identified in each row. The report never substitutes a lexical heuristic under those metric names.
- Browser citation click-through, isolated 3D rendering FPS and view-ready time are NOT MEASURED unless an actual supported browser experiment is supplied. A render loop callback or a valid citation URL alone does not establish those results.
- Complete run variance is retained. Identical deterministic rankings can produce zero run variance while host load changes timing. No threshold, frozen question or failing case was removed to raise scores.

## Reproduce and audit

See [evaluation setup](README.md). The default command dispatches actual specialist runs twice; aggregation alone reads results and does not replay inference.

```sh
python evaluation/run_eval.py
python evaluation/run_eval.py --phase final
python evaluation/run_eval.py --group retrieval --phase final
python evaluation/run_eval.py --aggregate-only --phase final
```

[Complete metric scorecard](stats-metric-scorecard.csv) · [Frozen input contract](CONTRACT.md) · [Specialist raw results](results/) · [Fix log](CHANGELOG.md)
