# Evaluation-driven application fixes

Baseline is frozen in `evaluation/baseline_results.json` before these changes. Regression counts below are local test outcomes, **not** replacements for final evaluation metrics. The orchestrator runs the unchanged full measurement suite twice after merging all fixes. Synthetic data only.

## Visual page diversity

- Problem: a preview vector is copied to each OCR chunk; the visual channel could spend its entire shortlist on one source page and crowd out independent text evidence.
- Change: select one representative per authorized source/version/page/image path **before** the visual top-K limit in PostgreSQL and in-memory search. Prefer OCR context, then longer text. Other retrieval channels retain their separate chunks and existing RRF weights/thresholds.
- Before: the new diversity regression failed (one page occupied both slots); the distinct-source/version test passed.
- After: `pytest tests/test_visual_diversity.py tests/test_hybrid_search.py tests/test_image_pipeline.py -q` — **35 passed**. PostgreSQL execution is covered in the final combined integration checks below.
- Full metric impact: pending the specialist final runs; no scores inferred from this regression.

## Multi-record numeric comparisons

- Problem: all numeric tokens were required within every individual chunk, so comparisons of two model/row identifiers could retrieve neither record.
- Change: explicit comparison/between/both/versus requests with multiple numeric tokens use a union of exact tokens, in SQL and in-memory channels. Ordinary single identifiers and multi-part card numbers retain exact all-token matching. Visual retrieval keeps its independent evidence proposal behavior.
- Before: comparison regression failed; exact-identifier/partial-number rejection passed.
- After: `pytest tests/test_numeric_retrieval.py tests/test_hybrid_search.py -q` — **26 passed**.
- Full metric impact: pending final specialist runs; this is not a relaxation of similarity thresholds.

## Native-text preview overhead

- Problem: generation and verification attached page previews even when reliable native prose already supplied the evidence; each duplicated text as expensive visual tokens.
- Change: omit long native-prose previews unless question/evidence mentions visual content, the page has recorded graphics, or related evidence includes OCR. Keep scanned/mixed/image anchors and short native headings. New PDF extraction records raster/vector graphics presence. Existing indexes without that flag retain conservative heading/visual-label checks; reprocessing records provides the stronger marker.
- Before: the new native-text test attached an unnecessary image; visual query-aware selection was unsupported (two failed, one passed).
- After: `pytest tests/test_evidence_images.py tests/test_image_pipeline.py -q` — **12 passed**. Tests cover charts, diagrams, scanned/mixed pages, short headings, explicit plotted-trend requests, and recorded graphics.
- Full latency/token/quality impact: pending unchanged specialist final runs. No timing improvement is claimed from unit tests.

### Numeric intent follow-through

- Multiple named alphanumeric units joined by `and/or` also use the exact-token union, even when a user does not say `compare`. Bare multipart numeric identifiers still require all parts.
- `pytest tests/test_numeric_retrieval.py -q` — **3 passed**, including the natural multi-unit phrasing reported by the retrieval specialist.

## Quote-only answer responsiveness

- Problem: an exact quotation was returned as supported even after the independent reviewer rejected the generated explanation, or when no explanation was produced. Exact substring provenance does not prove the quotation answers the requested object/field.
- Change: independently review quote-only fallbacks too. The review now explicitly rejects true but irrelevant facts and substitutions for missing objects/attributes. Keep exact immutable quote validation. A rejected quote-only review now abstains; this intentionally replaces the old unit-test expectation that any exact fallback quote should survive review failure.
- Before: an irrelevant service-interval quote passed a serial-number question (one new regression failed, one passed).
- After: `pytest tests/test_answer_responsiveness.py tests/test_worker.py tests/test_image_pipeline.py -q` — **28 passed**.
- Full abstention/false-refusal impact: pending final specialist inference. This remains model-based review, not a correctness guarantee.

## Aggregate query morphology

- Problem: the unrelated-query abstention gate counted plural `warranties` and expiry phrasing as missing subjects, rejecting relevant dated warranty records before generation.
- Change: compare simple plural and expiry/end inflections within that gate, excluding generic list verbs. Numeric terms and actual object/location terms remain meaningful. No retrieval weights or similarity thresholds changed.
- Before: the new warranty aggregate test failed; the absent-valve subject rejection passed.
- After: `pytest tests/test_aggregate_intent.py tests/test_hybrid_search.py tests/test_answer_responsiveness.py -q` — **28 passed**, including unrelated-subject rejection.
- Full aggregate answer accuracy: pending final specialist runs.

## Clear-cache HTTP method

- Problem: the Settings button passed `{method:'DELETE'}` as application data to a helper that always used POST for any body. The cache route accepts GET/DELETE, so the action failed with 405.
- Change: separate the browser helper's transport method from its JSON/form payload. The button now sends a bodyless DELETE with the existing household scope.
- After: `vitest run tests/client-api.test.ts` — **3 passed** (DELETE request, preserved GET/POST/multipart behavior, and API error propagation). The frozen baseline's failing UI transport behavior is the before evidence; the final security/UI probe will check the application outcome.
