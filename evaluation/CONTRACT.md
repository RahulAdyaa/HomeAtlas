# Frozen evaluation protocol

The 60 PDF questions in `testset.json` are preserved exactly. `question_annotations.json` adds independently authored synthetic household paths and source/page selectors. Current extraction chunk IDs must be resolved against those selectors: the older saved `reference_chunks` values may no longer match new ingestion output. Never rewrite the frozen testset to suit extracted chunks.

`scenarios.json` adds 20 fictional JSON records and 78 labeled questions: 38 typo/Hinglish variants, 20 clean queries, five identifiers, five no-match queries, three aggregates, three follow-ups, two location questions, and two additional unanswerable questions. Follow-ups include explicit conversation history; a stateless endpoint that does not accept history must report its limitation, rather than expand the question silently. JSON source records have no PDF page: `page=null` is deliberate, not a missing annotation. These are two suites: `pdf` (60), `household` (78), or `all` (138). Each metric reports the actual included sample size; no composite denominator silently substitutes 60 for 138 or vice versa.

`frozen_manifest.json` hashes every input. `protocol.frozen_dataset()` rejects modified inputs. The five PDFs were authored by `build_testset.py` (CC0 fictional content); their metadata, page count and file hashes are checked by the dataset audit. No live household data, uploads, credentials or real identifiers are needed.

## Specialist runner interface

Each specialist provides a separate script accepting:

```sh
python evaluation/<agent>_eval.py --phase baseline --run 1 --output evaluation/results/<agent>.json
python evaluation/<agent>_eval.py --phase baseline --run 2 --output evaluation/results/<agent>.json
```

The same interface supports `--phase final`. The central `run_eval.py` owner dispatches these scripts, accepts an optional `--group`, and assembles the scorecard after runs complete. `protocol.argument_parser`, `make_result` and `write_result` provide the common interface. Each result file is `{schema_version,agent,runs:[...]}`; writing replaces only the same phase/run record, preserving the other runs. Each run records commit, full app source hash, dataset fingerprint, configuration, timestamp, model identities, `metrics` and `per_question`. Every metric uses `{metric,value,n,status,reason}`; unavailable values must be null, status `NOT MEASURED`, and include a reason. Per-question rows include stable `id` and `run_id` (plus group-specific measurements). Runtime-observed model identities override published defaults and must be recorded explicitly.

Freeze `baseline_results.json` before application fixes. Baseline and final results retain their own app fingerprints. The fingerprint covers worker modules, libraries, server APIs, SQL and config; it is not limited to the three files covered by the previous harness.

## Two independent real inference runs

Use `protocol.cache_key(stage,payload,phase,run)` for generation, full-question, and judge response caches. The phase and run are part of the cache key, so run 2 cannot replay run 1 model answers. Generation is temperature zero if that is the application's setting; identical outputs are possible and do not prove replay. Record actual model calls and cache flags. Record consistency over three runs as `NOT MEASURED` unless a third real generation is explicitly executed (the full suite itself is required twice).

All worktrees must set the same absolute runtime and model directory:

```sh
export EVAL_SHARED_RUNTIME='/Users/rahuladya/Documents/New project/homeatlas/evaluation/runtime'
export MODEL_DIR='/Users/rahuladya/Documents/New project/homeatlas/data/models'
```

Use `protocol.shared_generation_slot()` around local LLM generation to avoid resource contention. Use `protocol.shared_judge_slot()` around free-tier judge requests, including retry/backoff. It serializes requests, respects a minimum interval and stays below the maximum of three judge agents. Store only timestamp metadata in shared locks. Judge response cache keys contain phase/run/model identity. Never print query text or credential values in shared logs. No free-tier judge key is configured at freeze time: dependent metrics must remain `NOT MEASURED` with that reason, not replaced by local heuristics under the same name. No paid fallback.

The shared locks prevent resource collisions; they are not a substitute for production concurrency benchmarks, which must label lock effects explicitly.
