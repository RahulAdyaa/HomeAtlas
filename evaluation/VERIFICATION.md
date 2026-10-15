# Independent verification

**Preflight only — final verification is pending.** This verifier has not generated evaluation scores, run model inference, or aggregated quality measurements. Application code, frozen inputs, metric definitions and other agents’ results were not changed.

The audited revision is `41a8a813276c8b26d0ef3011c2b609a1446843fa`. Frozen inputs and application source hashes match the recorded baseline application.

## Checks completed

- A temporary clean `git archive HEAD` passed the standard-library CLI help and dry-run commands without local dependencies, credentials or model files. Invalid group selection failed closed. No specialist was dispatched.
- Evaluation Python syntax parsed. The existing shared evaluation environment matches the pinned requirement files and passes `pip check`. This does **not** prove a fresh install or cross-platform package availability.
- `--check` rejected incomplete observations with exit code `2`; missing generation and outdated security coverage did not become a frozen baseline. This is an artifact-completeness check, not a failing application-security result.
- Repository-local ignore rules cover private environments, runtime/cache, uploads, database directories, model weights and dependencies. No forbidden tracked runtime artifacts were found.
- No unique local worker/auth secrets or generic API-key/private-key patterns were found in the inspected tracked text. The intentionally public loopback development database default also appears in setup/source/test files; it must not be mistaken for a newly leaked unique secret. Public deployment still requires fresh credentials and private services.
- The README screenshot exists and was visually inspected. Its fictional **Layout QA home** and **Layout browser fixture** match the synthetic browser script. It is an interface illustration, not a reliability measurement. No real private documents/logs were inspected.

## Pending before publication

- `--app-root` currently combines requested runtime settings with evaluator-checkout imports in some specialists. Owners were asked to make this fail closed on unequal application source hashes or consistently load/report the requested source. Current checkout/main application hashes are equal; existing observations must not be silently reinterpreted. Direct specialist absolute developer-path defaults also need portable replacements.
- The evaluation README links `stats-metric-scorecard.csv`, which is not yet present in this audited revision. Recheck after statistics output is generated.
- The Ollama generation tag is mutable. Record its artifact digest and provenance where observable; a post-run digest cannot prove an unrecorded historical artifact.
- Complete baseline/final result snapshots, final statistics and README tables are not yet available here. No final accuracy/CI/before-after parity verdict is issued.
- The full documented evaluation command requires a running app/worker, migrated disposable development database, installed system/Python/Node dependencies and local model artifacts. The independent verifier has **not** installed these from a fresh environment or run inference. CLI success must not be described as full clean-checkout reproduction.

The final pass must reconcile every README measurement and denominator with frozen results, validate confidence intervals and before/after claims, recheck links/screenshots, and scan the final proposed tracked/staged files for private data. Findings and evidence are also recorded in [verifier-agent.json](results/verifier-agent.json). No GitHub write action was performed.

## Post-fix source and documentation preflight

Reviewed the sole-fixer application diff after the immutable baseline. No concrete application regression was identified in this limited static review. Tenant/scope predicates and current-source/version checks remain in the retrieval/cache paths; owner authorization remains on cache clearing. Native prose image skipping retains explicit visual/OCR evidence markers. The answer review is another call to the same configured local model, not an independent external judge. Conservative identifier bypass does not establish universal zero-PII retention.

Independent targeted regressions passed: **25 Python tests** and **3 client transport tests**. These are unit/regression outcomes using fake engines or transport stubs, not RAG quality scores. No inference, live private cache payloads, uploaded user documents, or private query logs were accessed. Installed Next.js route-handler guidance was reviewed; the DELETE cache route returns JSON and preserves owner scope.

Main README final-phase commands and explicit clean-environment limitations are correct. Two reproducibility issues were routed to the statistics/document owner without changing frozen evaluator code:

- `evaluation/README.md` still gives bare baseline-default commands on the post-fix checkout. Use explicit `--phase final` here and separate historical baseline reproduction; otherwise specialist raw baseline rows can be replaced before immutable snapshot aggregation refuses the changed source.
- The runner computes `--app-root` from the parsed argument but exports it with `setdefault`. A conflicting preexisting `EVAL_APP_ROOT` can select a different child import root than the guard/interpreter validated. Existing final launches use consistent explicit environment, so these recorded runs are unaffected.

The central unequal-source guard and generation import/result/cache root handling have been repaired since the initial preflight. The household specialist’s direct fallback remains developer-specific; the documented central runner supplies the correct environment. Sampled Ollama artifact metadata must retain its historical timing qualification. The scorecard now exists in the main checkout, resolving the earlier pending-link artifact there.

Final measurements/statistics and README reconciliation are still pending. No final publication pass, fresh dependency installation, or full clean-machine inference claim is made. The generated `next-env.d.ts` working-tree difference was reported to the orchestrator and left untouched.
