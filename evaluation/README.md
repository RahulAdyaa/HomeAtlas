# HomeAtlas RAG evaluation

Run from the HomeAtlas app root:

```sh
python evaluation/run_eval.py
python evaluation/run_eval.py --modality chart
```

The launcher re-executes the isolated `evaluation/.venv` interpreter. A cached rerun prints the scorecard and regenerates JSON, CSV and Markdown without repeating completed inference. Supported slices: text, table, image, chart, scanned. Slice runs merge completed question results and preserve completed robustness results. All 60 questions are part of the default run.

## Fresh setup

Use Python 3.12 and the existing app's downloaded, revision-pinned model snapshots plus its loopback Ollama model (`qwen3-vl:4b-instruct`). Tesseract must be on PATH. The existing environment is already configured. To recreate a standalone evaluation environment, run these commands from the app root (only evaluation is written):

```sh
python3.12 -m venv evaluation/.venv
PIP_CACHE_DIR="$PWD/evaluation/cache/pip" evaluation/.venv/bin/python -m pip install -r evaluation/requirements.lock.txt
python evaluation/run_eval.py
```

The delivered environment uses a read-only `.pth` reference to the app worker's installed packages; new RAGAS packages are installed only under evaluation. `requirements.lock.txt` contains all runtime versions so a fresh venv can instead install them independently. Application model snapshots are read, never downloaded or modified by the runner. The runtime versions are recorded in runtime_versions.json. Original fixture creation requires Arial.ttf at the macOS system path used by this machine; supplied fixture PDFs/testset are portable and need no font regeneration.

## Complete the missing free-tier judge metrics

No supported free-tier judge credential was configured during this run. Therefore seven RAGAS judge metrics and external vision judging are **unavailable**, not estimated. Answer similarity is actual RAGAS with the app BGE embedding model.

Create `evaluation/.env` privately (never commit it):

```dotenv
OPENROUTER_API_KEY=your-key
EVAL_JUDGE_MODEL=openrouter/free
```

Only `openrouter/free` or model IDs ending `:free` are accepted. Use an explicitly selected free vision-capable model to make provider behavior reproducible; the free router may select different providers and the returned model is retained in the raw cache. The adapter submits original fictional evaluation data only. Never insert real household documents into this public/free provider benchmark without reviewing their privacy requirements.

Then rerun the default command or each `--modality` slice. Missing judge metrics resume; completed model answers and successful individual metrics remain cached. Requests retry 429/5xx/network failures up to five times with exponential backoff and Retry-After handling. Failed requests are not cached as success. Successful raw judge responses, model IDs and usage are cached in `evaluation/cache/judge/`; metric scores are cached separately. There is no paid-model fallback. The live external adapter is unverified because no credential is present.

## Output

- `RAG_EVALUATION_REPORT.md`: all 12 requested component groups, scorecard, modality/K tables, limitations and recommendations.
- `testset.json`: 60 questions with authored references, exact source pages/regions and mapped app chunk IDs.
- `fixtures/*.pdf`: five four-page original CC0 PDFs, manifest, and visually reviewed contact sheet.
- `results.json`: complete question-level outputs, ranking and generation metrics, citations, tokens and timing.
- `results.csv`: flat question-level scores.
- `cache/`: resumable extraction, embeddings, reranking, generation and judge results. Generated model calls use seed-fixed fixture ordering and temperature zero; the unchanged app does not send an inference seed to Ollama.
- `runtime/robustness/`: low-resolution, rotated, noisy/blurred and mixed-language scan variants.
- `run.log`: full initial run and terminal scorecard; `rerun.log` and `slice.log`: repeatability evidence.

Application source, database, customer uploads, household state, configuration and existing tests remain read-only. Evaluation calls the actual extraction, embedding, ranker/reranker and answer functions on an isolated in-memory corpus. It **does not test the app's HTTP upload/queue/DB or browser viewer**. Numeric trust scores, structured table extraction, dedicated figure detection and image captions do not exist in the current app; this limitation is distinct from missing judge credentials.

The report's operational diagnostic index has a disclosed four-metric denominator. It is not an overall semantic quality score. Missing scores remain `null`/N/A. Raw token-matching diagnostics never replace RAGAS correctness or faithfulness.

To invalidate a run after evaluation logic changes, increment the explicit `evaluation-schema-v2` cache version in run_eval.py. App source and fixture-builder changes automatically invalidate cache keys. Failed local model calls returning no result are not cached as success; extractive fallback questions are retried on the next run. To explicitly repeat a completed question, remove only its evaluation generation/question cache entries; no app data needs deletion.

Formula checks:

```sh
evaluation/.venv/bin/python evaluation/test_metrics.py
```

## Hybrid and semantic-cache regression benchmark

Run `worker/.venv/bin/python evaluation/hybrid_eval.py` from the repository root after applying migrations and installing the pinned multilingual model. This reuses the ranking metrics extracted from the original harness into `retrieval_metrics.py`, and exercises the production PostgreSQL channel modules. It produces `HYBRID_EVALUATION_REPORT.md` and `hybrid-results.json` from the independently labeled fictional corpus in `hybrid_testset.py`. No user documents are read. See the report for limitations and unmet targets; do not combine these numbers with the older PDF end-to-end evaluation.
