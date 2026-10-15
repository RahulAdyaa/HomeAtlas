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
