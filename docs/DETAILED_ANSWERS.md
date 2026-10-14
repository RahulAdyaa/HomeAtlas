# Detailed answers with PDF visual evidence

14 October 2026. This change replaces the two-short-quotation limit with evidence-reviewed explanations. Qwen can produce up to eight sections and eight source quotations, covering relevant definitions, procedures, equations and comparisons. The model emits tables as structured columns and rows, which the worker converts into table markup. A small safe renderer displays headings, emphasis and tables without executing HTML.

Retrieval retains the existing hybrid ranking, then expands context with adjacent pages from the same authorized, current source (maximum 12 chunks). Generation receives up to four bounded-resolution source page images, plus an optional query image. Existing PDF page previews can be used immediately; this change does not require uploading the original again. It does not implement dedicated figure cropping or structured table extraction.

Every section references source quotations. Python verifies those quotations against immutable chunk text, and a second local Qwen request reviews every section against its referenced quotations and labelled page images. Visual-only facts use an exact page title/caption quotation as a provenance anchor. This proves source identity; semantic visual interpretation is model-reviewed, not independently or mathematically certified. Common unsupported speculative phrasing is rejected before review, and obvious instruction tails are excluded from model text context. These conservative checks supplement rather than replace model review. Unsupported sections are omitted, with a notice when part of a proposed explanation fails review. If review fails entirely, verified direct quotations remain available. Missing evidence still abstains and conflicting records retain a visible conflict status.

Next.js independently rechecks household membership, canonical source/version/chunk identities, and exact quotation substrings. The answer displays deduplicated, authenticated source-page thumbnails that open the existing evidence drawer. These are whole original pages, not claims that every page is a detected diagram. Table values and visual descriptions can still be wrong if both model passes make the same mistake; inspect the original evidence for important decisions.

More context, source images and the review request increase latency and memory use. The default worker HTTP timeout is now five minutes; generation and review each have bounded timeouts. This is the local 4B model profile, not a production throughput claim.

## Verification commands

- `worker/.venv/bin/python -m pytest tests/test_worker.py -q`: includes explanation-reference rejection and review-failure fallback.
- `node --env-file=.env.local node_modules/vitest/vitest.mjs run`: authorization, malicious-worker evidence rejection and credit invariants.
- `PYTHONPATH=. worker/.venv/bin/python scripts/detailed-answer-check.py`: actual local Qwen explanations and chart-reading checks against original CC0 evaluation PDFs.
- `node scripts/detailed-answer-browser.mjs`: actual authenticated answer and citation endpoints, then desktop/phone rendering of that real response. The UI replay avoids an extra inference request and charge.
- `npm run build`: production compilation and private-artifact exclusion.

The earlier 60-question evaluation predates this answer/context change. Its scores are historical results and do not measure the new pipeline. This focused verification does not replace rerunning the full benchmark.

## Focused verification results

- 58 backend tests passed; two additional renderer tests passed for table cells and HTML escaping.
- 14 Python unit tests passed, including invalid references, review fallback, structured tables and speculative-prose rejection.
- Real authenticated detailed-answer API, independent citation checks, private preview loading, and desktop/phone evidence-drawer checks passed without browser exceptions or horizontal page overflow.
- Final combined local-model check passed for multi-page text (1,136 characters, four citations), a structured table (460 characters), and chart interpretation (955 characters). The chart check verifies 65 kWh; the table check verifies 71 W and USD values.
- Actual local-model prompt-injection and conflicting-evidence checks passed.
- TypeScript and production build passed; the build artifact excludes private environment files and model weights.

These are focused implementation checks on fictional records, not a guarantee for arbitrary uploaded documents.
