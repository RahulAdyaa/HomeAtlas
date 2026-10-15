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

## Python hashing compatibility

- Problem: ingestion used `hashlib.file_digest`, unavailable on the advertised Python 3.10 runtime.
- Change: compute the same SHA256 digest with bounded 1 MiB reads, avoiding that version-specific API.
- Before: the original call cannot execute on Python 3.10 (API absent); the task environment itself runs Python 3.12, so no full Python 3.10 runtime validation is claimed.
- After: `pytest tests/test_file_hash.py -q` — **2 passed**, including removal of `hashlib.file_digest` and multi-block/empty-file integrity.

## Personal identifier cache retention

- Problem: the frozen security test found a fictional personal-card serial answer persisted in the optional response cache. Household/user isolation passed separately; isolation does not satisfy zero identifier retention.
- Change: bypass cache lookup/write for personal-card identifier requests and detect identifier-bearing answer/citation/record-fact content even under generic questions. Ordinary household locations and appliance model/serial requests can still cache. Increment the cache policy generation, and remove sensitive legacy entries on authenticated lookup/write without logging their contents.
- Before: the specialist baseline persisted its synthetic card serial answer (see the frozen security result, not a new estimate).
- After: `pytest tests/test_cache_privacy.py tests/test_hybrid_search.py -q` — **35 passed**. Real PostgreSQL `HOMEATLAS_DB_TESTS=1 pytest tests/test_eval_fixes_db.py tests/test_semantic_cache.py -q` — **9 passed**, covering no sensitive write, removal of a synthetic legacy sensitive entry, populated appliance-cache exact hits, same-household user isolation, cross-household isolation, move/delete invalidation, TTL/LRU, SQL visual diversity and numeric unions.
- Deployment action: stop old application/worker processes, clear the **ephemeral** `answer_cache` once without selecting payloads, then start the new code. This purges untouched legacy scopes too. It removes no uploaded source/item records. No schema migration is required.
- Tradeoff: the frozen security fixture assumes the same personal-card serial requests should generate cache hits. Those hit assumptions are intentionally incompatible with identifier bypass; report their failures honestly and cite the separate populated non-sensitive cache regressions rather than changing the frozen tests. Cached-variant hit rate may fall.
- Limits: this is a conservative personal-identifier policy, not a guarantee that arbitrary names, addresses or every international identifier format can never occur in free-form cached prose. Authorized original documents remain in their private source store.

## Review independence and recommended work

The answer-support check is a separate verification call using the **same configured local Qwen model**, not an independent external benchmark judge. External-judge-dependent evaluation metrics remain NOT MEASURED when no judge is configured.

Recommended, not done in this narrow fix pass:

- Conversation history and referent resolution: current stateless API does not safely resolve arbitrary follow-ups; this needs a new explicit conversation contract and isolation tests.
- General structured table/figure/chart parsing and robust degraded-scan recovery: existing OCR/native extraction and visual review cannot guarantee every chart cell, label or blurred identifier. A parser redesign would exceed a safe bug fix.
- Calibrated numerical trust scores: categorical confidence cannot support AUROC/Brier/ECE or reliability claims without a defined probability and separate calibration data.
- Universal PII zero retention: broader policy/classification and data lifecycle controls are needed beyond the conservative identifier bypass above.
- Strictly beating fuzzy-only typo MRR when that channel already scores 1.0 is mathematically impossible on this frozen subset; no metric, gold, threshold, or weight was changed to disguise that limit.

## Combined regression verification

- `HOMEATLAS_DB_TESTS=1 python -m pytest tests -q` — **92 passed**, with five existing PyMuPDF/SWIG deprecation warnings.
- `npm test` — **87 passed across 15 files**.
- `npm run typecheck` — **passed** (exit 0).
- Real database checks used freshly generated, disposable synthetic households and cleaned them up. No live user documents, query logs, cache payloads, or identifiers were inspected.
- Exact commands and outcomes are saved in `evaluation/results/fixer-agent.json`. Frozen specialist evaluation scripts, inputs, score formulas, retrieval thresholds and weights were not edited. These are app regression results; the final RAG measurements remain the specialists' responsibility.

## Fix cycle 2: cited-evidence alignment

Candidate `434af147…` produced correct generated statements for two synthetic text questions but the support review returned no accepted sections. Its review context included unrelated scan quotes/images that no proposed section cited. Separately, accepted answers returned all generated quotes as citations even when the accepted section used only one.

- Change: support review receives only quotes referenced by the proposed sections and their associated images. Original quote indices stay stable through review. Final output retains only quotes used by accepted sections, renumbers displayed citations consecutively, and preserves source/version/page/bbox metadata. Referenced visual evidence stays attached. Exact-quote checks and the question-responsiveness review remain in place.
- Before: four new alignment/citation regressions fail when run against the pre-cycle-2 modules from `ecb6aef`.
- After: the focused alignment/responsiveness/worker suite passes **24 tests**, including a fifth control that preserves a referenced visual image. Full Python with disposable PostgreSQL fixtures: **97 passed**. TypeScript: **87 passed in 15 files**. Typecheck: **passed**.
- Controlled replay: reconstruct the two original synthetic review payloads from saved generated output/corpus and verify their original model-cache identities. Run real, uncached old-versus-filtered local Qwen reviews with identical sections, prompt and model settings under the shared generation lock. Text-02 changes from rejected with two unused images to accepted with zero images; text-03 changes from rejected with four unused images to accepted with zero images. This supports unused-context interference in these cases. The full comparison makes **eight actual HTTP calls** across two positive cases and two negative controls; raw decisions, token usage and request hashes are preserved in the fixer's result artifact. These controlled checks are not replacements for the full frozen evaluation.
- Negative controls: an irrelevant exact quotation is rejected by both versions. **An unsupported numerical claim of 99 months against an 18-month source is accepted by both versions.** That preexisting same-model review weakness remains unresolved; this patch does not establish universal numerical grounding or independent-judge reliability. Report it honestly. No score thresholds, prompts, frozen questions, metric code or gold data were altered.
- Deployment: restart merged application/worker code. No schema migration or reindex is needed for this cycle. The orchestrator must rerun the full final suite twice with the new source fingerprint; partial results from the earlier candidate remain historical evidence.

### Fix cycle 2 follow-through: conservative text-only numeric coverage

The unsupported 99-month claim exposed by the alignment control was accepted by the same-model reviewer both before and after evidence filtering. The orchestrator authorized a separate bounded guard before the next source freeze.

- Change: for each proposed section, compare numeric literals and alphanumeric identifiers with **that section's own referenced quotes**. Reject new unsupported literals before model review when no referenced image needs visual inspection. Normalize common decimal/thousands formatting, numeric date components, grouped long digit identifiers, and a simple letter-prefix identifier separator. Preserve identifier leading zeroes and arbitrary internal separators. Review only eligible sections and their evidence, preserving original indices. No prompt or model threshold changed.
- Before: the saved actual Qwen control accepts `T1 warranty 99 months` against an `18 months` source. After: the same control is rejected deterministically with **zero HTTP calls**. The final retained guard replay makes **three actual HTTP calls across four cases**: both previously refused correct synthetic sections still pass local Qwen, and the irrelevant-quote control still fails. Detailed final decisions and usage are in the fixer's result artifact. These are diagnostic controls, not the final benchmark.
- Tests: focused numeric/alignment/responsiveness suite **19 passed**; complete Python with real disposable PostgreSQL fixtures **109 passed**; TypeScript **87 passed across 15 files**; typecheck **passed**. Coverage includes supported 18 versus unsupported 99, zero-sensitive identifiers, bounded identifier/date/quantity formatting, both cited 18+36 values, unverified 54 derived value, per-section isolation, referenced visuals, and section-index preservation.
- Arithmetic policy: a new derived number absent from cited text is not independently validated here and abstains. This can reduce completeness for calculated totals or differences. Existing structured saved-record/direct-fact paths were not changed.
- Limits: literal presence does not prove correct object/value pairing, units or date semantics. Spelled-out numeric claims and arbitrary numeric formats are not comprehensively validated. Referenced chart/OCR/image facts remain with visual review because they may be missing from the extracted text; that reviewer can still err. No universal numerical truth or zero-hallucination guarantee is claimed.
- Deployment: restart merged code; no schema migration/reindex. Run both complete final evaluation passes against the new frozen source hash.
