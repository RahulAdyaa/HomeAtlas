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
