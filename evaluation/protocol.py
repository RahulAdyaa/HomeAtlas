"""Shared evaluation contract. No application imports, network calls, or private-data reads."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
EVALUATION = Path(__file__).resolve().parent
SCHEMA_VERSION = 1
SEED = 741


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_dataset() -> dict:
    """Fail closed on edited fixtures, including original and supplemental questions."""
    manifest = json.loads((EVALUATION / 'frozen_manifest.json').read_text())
    for name, expected in manifest['files'].items():
        path = EVALUATION / name
        if not path.is_file() or file_sha(path) != expected:
            raise RuntimeError(f'Frozen dataset mismatch: {name}')
    if digest(manifest['files']) != manifest['dataset_fingerprint']:
        raise RuntimeError('Frozen manifest fingerprint mismatch')
    return manifest


def app_fingerprint(root: Path | None = None) -> dict:
    """Cover all worker modules, config, SQL, libraries and server API routes."""
    root = (root or EVALUATION.parent).resolve()
    patterns = ['worker/**/*.py', 'lib/**/*.ts', 'app/api/**/*.ts', 'db/*.sql',
                'config/**/*.json', 'worker/**/*.json', 'package.json', 'package-lock.json',
                'worker/requirements*.txt']
    paths = sorted({p for pattern in patterns for p in root.glob(pattern)
                    if p.is_file() and not any(x in p.parts for x in ['.venv', '__pycache__'])})
    files = {str(p.relative_to(root)): file_sha(p) for p in paths}
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True,
                            text=True, check=True).stdout.strip()
    return {'app_commit': commit, 'app_source_fingerprint': digest(files), 'app_files': files}


def model_identities(root: Path | None = None) -> dict:
    """Return published defaults only; do not import config/load .env secrets."""
    import ast
    root = root or EVALUATION.parent
    tree = ast.parse((root / 'worker/config.py').read_text())
    keys = {'TEXT_EMBEDDING_MODEL', 'TEXT_EMBEDDING_REVISION', 'RERANKER_MODEL',
            'RERANKER_REVISION', 'IMAGE_EMBEDDING_MODEL', 'IMAGE_EMBEDDING_REVISION',
            'GENERATION_MODEL', 'OCR_BACKEND', 'OCR_LANGUAGES'}
    defaults = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and len(node.args) >= 2:
            if isinstance(node.args[0], ast.Constant) and node.args[0].value in keys:
                if isinstance(node.args[1], ast.Constant):
                    defaults[node.args[0].value] = node.args[1].value
    return {'published_defaults': defaults,
            'requirement': 'Each actual runner must also record observed engine identities and overrides.'}


def argument_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--phase', choices=['baseline', 'final'], default='baseline')
    parser.add_argument('--run', choices=[1, 2], type=int, default=1)
    parser.add_argument('--output', type=Path, required=True)
    return parser


def run_namespace(phase: str, run: int, root: Path | None = None) -> str:
    if phase not in {'baseline', 'final'} or run not in {1, 2}:
        raise ValueError('Only baseline/final and independent run 1/2 are supported')
    return digest([frozen_dataset()['dataset_fingerprint'],
                   app_fingerprint(root)['app_source_fingerprint'], phase, run])


def cache_key(stage: str, payload: Any, phase: str, run: int,
              root: Path | None = None) -> str:
    """Use for generation/question/judge caches. Two runs cannot share an inference."""
    return digest([run_namespace(phase, run, root), stage, payload])


def metric(name: str, value: float | int | None, n: int, *, reason: str | None = None,
           **extra: Any) -> dict:
    if n < 0 or (value is None and not reason):
        raise ValueError('Unavailable metrics require an explicit reason; n must be nonnegative')
    return {'metric': name, 'value': value, 'n': n,
            'status': 'NOT MEASURED' if value is None else 'MEASURED',
            'reason': reason, **extra}


def make_result(agent: str, phase: str, run: int, metrics: list[dict],
                per_question: list[dict], config: dict | None = None,
                root: Path | None = None) -> dict:
    dataset = frozen_dataset()
    return {'schema_version': SCHEMA_VERSION, 'agent': agent,
            'phase': phase, 'run': run, 'run_id': f'{phase}-run-{run:02}',
            'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
            'dataset_fingerprint': dataset['dataset_fingerprint'],
            **app_fingerprint(root), 'config': config or {},
            'models': model_identities(root), 'metrics': metrics, 'per_question': per_question}


def write_result(path: Path, result: dict) -> None:
    """Agent owns this file; preserve all other phase/run records within it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(path.read_text()) if path.exists() else {'schema_version': 1, 'runs': []}
    if old.get('runs') is None:
        raise ValueError('Expected envelope {schema_version, runs: [...]}')
    runs = [r for r in old['runs'] if (r['phase'], r['run']) != (result['phase'], result['run'])]
    runs.append(result)
    payload = {'schema_version': SCHEMA_VERSION, 'agent': result['agent'],
               'runs': sorted(runs, key=lambda r: (r['phase'], r['run']))}
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False, default=str) + '\n')
    temporary.replace(path)


@contextmanager
def shared_judge_slot(min_interval_seconds: float = 4.0):
    """Global cross-worktree process lock; serial judge calls obey <=3 concurrency.

    Hold across the actual HTTP request, including retry/backoff. No query text or
    credentials are persisted. A single request at once is intentionally conservative.
    Cache raw judge responses separately by cache_key(..., phase, run).
    """
    runtime = Path(os.environ.get('EVAL_SHARED_RUNTIME', str(EVALUATION / 'runtime')))
    shared = Path(os.environ.get('EVAL_SHARED_STATE', str(runtime / 'coordination')))
    shared.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = shared / 'judge.lock'
    state = shared / 'judge-last-start.json'
    with lock.open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            last = json.loads(state.read_text()).get('monotonic', 0) if state.exists() else 0
            delay = max(0.0, min_interval_seconds - (time.monotonic() - last))
            if delay:
                time.sleep(delay)
            state.write_text(json.dumps({'monotonic': time.monotonic()}))
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def questions(suite: str = 'all') -> list[dict]:
    """Return annotated copies. Frozen original questions are never rewritten."""
    frozen_dataset()
    if suite not in {'pdf', 'household', 'all'}:
        raise ValueError('suite must be pdf, household, or all')
    base = json.loads((EVALUATION / 'testset.json').read_text())['questions']
    annotations = {q['id']: q for q in json.loads((EVALUATION / 'question_annotations.json').read_text())['annotations']}
    base = [{**q, **annotations[q['id']], 'suite': 'pdf'} for q in base]
    supplement = [{**q, 'suite': 'household'} for q in json.loads((EVALUATION / 'scenarios.json').read_text())['questions']]
    return base if suite == 'pdf' else supplement if suite == 'household' else base + supplement


@contextmanager
def shared_generation_slot():
    """Serialize local model generation across evaluators to avoid model contention.

    Set EVAL_SHARED_RUNTIME to one absolute directory in all worktrees. This is a
    resource lock, not a response cache; generation for run 1 and 2 remains separate.
    """
    runtime = Path(os.environ.get('EVAL_SHARED_RUNTIME', str(EVALUATION / 'runtime')))
    shared = runtime / 'coordination'
    shared.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (shared / 'generation.lock').open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def canonical_chunks(chunks: list, source_key: str, title: str,
                     location_path: str, tags: list[str] | None = None) -> list[dict]:
    """Mirror ingestion location prefixes BEFORE embedding; preserve visual evidence.

    Pass actual extracted chunks. Returned rows are unembedded; callers embed row.text
    and attach the app engine's observed embedding identities. Source/page selector
    resolution uses fixture_source_id, while production-like UUIDs remain stable.
    """
    from dataclasses import asdict, is_dataclass
    from uuid import NAMESPACE_URL, uuid5
    def ident(name: str) -> str:
        return str(uuid5(NAMESPACE_URL, 'https://homeatlas.invalid/evaluation/' + name))
    rows = []
    for index, chunk in enumerate(chunks):
        row = asdict(chunk) if is_dataclass(chunk) else dict(chunk)
        metadata = dict(row.get('metadata') or {})
        original = metadata.get('content_text', row.get('text', ''))
        # Exactly one prefix; callers must not pass already prefixed text without metadata.
        row['text'] = f'Location: {location_path}\n\n{original}'
        row['metadata'] = {**metadata, 'content_text': original, 'location_path': location_path,
                           'tags': list(tags or []), 'synthetic': True}
        row.update(id=ident(f'chunk/{source_key}/page-{row.get("page")}/index-{index}'),
                   source_id=ident('source/' + source_key),
                   version_id=ident('version/' + source_key + '/v1'),
                   fixture_source_id=source_key, source_modality=source_key,
                   title=title, location_path=location_path, tags=list(tags or []))
        rows.append(row)
    return rows


def relevant_chunk_ids(question: dict, corpus: list[dict]) -> list[str]:
    """Map authored gold source/page selectors after actual ingestion, without text judging."""
    if question.get('unanswerable'):
        return []
    mapping = question.get('ground_truth_mapping') or {}
    source = mapping.get('source_id', question.get('modality'))
    pages = mapping.get('pages', question.get('source_pages', []))
    if question.get('suite') == 'household' or question.get('relevant_document_ids'):
        ids = set(question.get('reference_chunks', []))
        sources = set(question.get('relevant_document_ids', []))
        return [c['id'] for c in corpus if c['id'] in ids or c.get('source_id') in sources]
    return [c['id'] for c in corpus
            if c.get('fixture_source_id', c.get('source_id')) == source and c.get('page') in pages]
