# Reproduce the HomeAtlas evaluation

The commands below evaluate the current application with the explicit `--phase final` option and execute the frozen synthetic suite twice using separate run namespaces. They dispatch actual ingestion, retrieval, generation, household/cache and security evaluators sequentially, then compute confidence intervals and assemble the report. This can take several hours on a 16 GB development computer. Completed work resumes only within the same phase/run; a second run cannot reuse the first run's model answer. The frozen CLI defaults to `baseline` when the phase is omitted, so always specify the phase on the current checkout.

Run from the repository root with Python 3.12, PostgreSQL and the app/worker running as described in the main README. The database must have the repository migrations applied. The runners create and delete disposable `example.invalid` accounts and fictional documents; use a development database. Existing household documents are never the evaluation corpus.

```sh
python3.12 -m venv evaluation/.venv
evaluation/.venv/bin/python -m pip install -r evaluation/requirements.lock.txt
evaluation/.venv/bin/python -m pip install -r evaluation/requirements-metrics.txt
export EVAL_APP_ROOT="$PWD"
export MODEL_DIR="$PWD/data/models"
export EVAL_SHARED_RUNTIME="$PWD/evaluation/runtime"
export EVAL_PYTHON="$PWD/evaluation/.venv/bin/python"
python evaluation/run_eval.py --dry-run --phase final
python evaluation/run_eval.py --phase final
```

Use the app's revision-pinned downloaded models and local Ollama `qwen3-vl:4b-instruct`. Tesseract must be installed with `eng` and `hin` languages. The runner does not silently download a substitute model. The app/worker configuration remains in ignored local environment files; never commit credentials. Node.js and installed app dependencies are required for authenticated HTTP probes.

```sh
python evaluation/run_eval.py --group retrieval --phase final
python evaluation/run_eval.py --group A --group G --phase final
python evaluation/run_eval.py --phase final
python evaluation/run_eval.py --aggregate-only --phase final
python evaluation/run_eval.py --check --phase final
```

`--group` accepts `ingestion`, `retrieval`, `generation`, `homeatlas`, `security`, `stats`, or A–L, and can be repeated/comma-separated. `--run 1` or `--run 2` runs a single pass, but a frozen baseline/final snapshot still requires both complete passes from every specialist. Group L/stats aggregates existing observations. `--aggregate-only` does not perform a new evaluation. A partial suite returns exit code 2 and writes only an ignored completeness diagnostic, never `baseline_results.json` or `final_results.json`. Missing measurements are null with `NOT MEASURED` and a reason.

`--app-root`, `--results-dir`, `--result AGENT=PATH` and `--python` support isolated evaluation worktrees. They are optional for an ordinary checkout. Before dispatch, the evaluator checkout and requested app root must have identical application source hashes; propagate the same application commit into an isolated worktree first. A mismatch fails before inference because specialist import roots differ. Always set `EVAL_APP_ROOT` to the same absolute directory as `--app-root` when supplying that option: the frozen runner does not replace an already exported, conflicting `EVAL_APP_ROOT`, and its children may otherwise import a different checkout. Update `MODEL_DIR`, `EVAL_SHARED_RUNTIME` and `EVAL_PYTHON` consistently when changing checkouts. Aggregate/check operations compare recorded hashes against the requested app root without importing application code. Published provenance uses repository-relative paths. Do not expose private paths, settings dumps or actual user content in results.

Historical baseline reproduction requires an isolated application checkout matching the source fingerprint recorded in `baseline_results.json`, together with the same frozen evaluator, models, dependencies and gold inputs. Use a separate development database, runtime, raw-results directory and disposable artifact copy. Set the phase explicitly to `baseline` only in that historical environment. Never dispatch baseline evaluation against the fixed application or into the published `evaluation/results` directory: specialist runs write their raw results before the immutable aggregate snapshot checks for replacement. A fresh reproduction is a separate experiment with new timestamps, not a replacement for the sealed original baseline; preserve the published baseline and its raw records.

No free-tier external judge key was configured for the recorded evaluation. Judge-dependent RAGAS, claim faithfulness, semantic correctness and image hallucination metrics remain **NOT MEASURED**. Local embeddings, custom token alignment, exact facts and canonical citations are separately named diagnostics. No paid fallback or invented scores are used. The historical pre-orchestration runner is retained in Git history. It predates the frozen input contract and must not regenerate this suite.

The frozen 138-question corpus, raw specialist results, all metric definitions, and the actual observation sources are described in [CONTRACT.md](CONTRACT.md) and [RAG_EVALUATION_REPORT.md](RAG_EVALUATION_REPORT.md). [stats-metric-scorecard.csv](stats-metric-scorecard.csv) includes every specialist metric, both raw run values, sample sizes, variance, confidence interval or its explicit unavailability reason. The report shows the main tables; it does not hide the full configuration grid.

Statistical formula and completeness checks:

```sh
evaluation/.venv/bin/python -m unittest discover -s evaluation -p 'stats_test_*.py'
```

A snapshot is frozen only after source/data hashes, full question/probe coverage and metric status/denominator checks pass. It records raw run digests. Attempts to overwrite that snapshot with different observations fail closed. Application fixes occur only after the complete baseline is frozen. Final measurements use the same gold and metric code, with two new independent passes.
