"""Statistical assembly of specialist observations; never changes metric definitions.

Raw values remain owned by their specialists. A confidence interval is produced
only where raw samples reproduce every published per-run point estimate.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
from typing import Any

from protocol import SEED, app_fingerprint, digest, frozen_dataset, questions

AGENTS = ('testset-agent', 'ingestion-agent', 'retrieval-agent', 'generation-agent',
          'homeatlas-agent', 'security-system-agent')
INFERENCE_AGENTS = AGENTS[1:]


def load_sources(results_dir: Path, overrides: dict[str, Path] | None = None) -> dict:
    sources = {}
    for agent in AGENTS:
        path = (overrides or {}).get(agent, results_dir / (agent + '.json'))
        if path.is_file():
            payload = json.loads(path.read_text())
            sources[agent] = {'path': path, 'payload': payload}
    return sources


def select_runs(source: dict, phase: str) -> list[dict]:
    return sorted((r for r in source['payload'].get('runs', []) if r.get('phase') == phase),
                  key=lambda r: r.get('run', 0))


def assess_completeness(sources: dict, phase: str, app: Path) -> dict:
    frozen = frozen_dataset()['dataset_fingerprint']
    current = app_fingerprint(app)['app_source_fingerprint']
    expected_ids = {q['id'] for q in questions()}
    expected_pdf = {q['id'] for q in questions('pdf')}
    issues, checks = [], []
    for agent in AGENTS:
        source = sources.get(agent)
        if not source:
            issues.append(f'{agent}: missing result file')
            continue
        if source['payload'].get('agent') != agent:
            issues.append(f'{agent}: envelope agent mismatch')
        # The testset agent is an input audit, not an inference pass. Its original
        # baseline audit is valid for final only when the frozen dataset is identical.
        runs = select_runs(source, 'baseline' if agent == 'testset-agent' else phase)
        wanted = [1] if agent == 'testset-agent' else [1, 2]
        for number in wanted:
            found = [r for r in runs if r.get('run') == number]
            label = f'{agent}/{phase}/run-{number}'
            if len(found) != 1:
                issues.append(f'{label}: expected exactly one record, found {len(found)}')
                continue
            r = found[0]
            before = len(issues)
            if r.get('dataset_fingerprint') != frozen:
                issues.append(f'{label}: frozen dataset fingerprint mismatch')
            if agent != 'testset-agent' and r.get('app_source_fingerprint') != current:
                issues.append(f'{label}: source fingerprint differs from current application')
            config = r.get('config', {})
            if config.get('partial') or config.get('complete') is False:
                issues.append(f'{label}: specialist marks run partial/incomplete')
            rows = r.get('per_question', [])
            ids = [q.get('id') for q in rows]
            if agent in {'testset-agent', 'retrieval-agent', 'generation-agent'}:
                expected = expected_pdf if agent == 'generation-agent' else expected_ids
                if set(ids) != expected or len(ids) != len(expected):
                    issues.append(f'{label}: question ID coverage incomplete or duplicated ({len(ids)} observed, {len(expected)} required)')
            if agent == 'generation-agent':
                if not config.get('custom_bertscore'):
                    issues.append(f'{label}: reference/BERTScore postprocessing not complete')
                if number == 2 and len(r.get('three_run_consistency_sample', [])) != 5:
                    issues.append(f'{label}: predeclared third-pass consistency sample incomplete')
            if agent == 'retrieval-agent':
                robust = config.get('robustness', [])
                if sum(q.get('kind') == 'image-query' for q in robust) != 5 or sum(q.get('kind') == 'degraded_scan' for q in robust) != 6:
                    issues.append(f'{label}: image/degraded scan observations incomplete')
                if config.get('inference_replayed_from_other_run') is not False:
                    issues.append(f'{label}: independent-inference attestation missing')
            if agent == 'security-system-agent':
                if config.get('complete') is not True:
                    issues.append(f'{label}: evaluator has not attested expanded probe completion')
                expected_probes = config.get('expected_live_probe_ids', [])
                actual_probes = [q.get('id') for q in rows if q.get('group') == 'J/K-live']
                if len(expected_probes) != 27 or set(actual_probes) != set(expected_probes) or len(actual_probes) != 27:
                    issues.append(f'{label}: expanded security probe ID coverage differs from its 27-probe contract')
                if config.get('generation_partial') is not False or config.get('generation_rows') != 60:
                    issues.append(f'{label}: performance import lacks complete same-pass PDF observations')
                if config.get('generation_app_source_fingerprint') != current:
                    issues.append(f'{label}: imported generation source fingerprint mismatch')
            if agent in {'homeatlas-agent', 'ingestion-agent'}:
                # These groups run supplemental upload/cache/parser probes. Check
                # the owner's declaration against the raw IDs, not a filename.
                if config.get('complete') is not True:
                    issues.append(f'{label}: evaluator has not explicitly attested complete probe coverage')
                if agent == 'homeatlas-agent':
                    expected_probes = config.get('expected_probe_ids', [])
                    expected_count = 95
                else:
                    coverage = config.get('coverage_attestation', {})
                    expected_probes = coverage.get('required_probe_ids', [])
                    expected_count = 186
                    if coverage.get('owner') != agent or not coverage.get('checks') or not all(coverage['checks'].values()):
                        issues.append(f'{label}: owner coverage checks absent or failed')
                if len(expected_probes) != expected_count or set(ids) != set(expected_probes) or len(ids) != expected_count:
                    issues.append(f'{label}: raw probe IDs differ from explicit {expected_count}-probe owner contract')
            if not r.get('metrics'):
                issues.append(f'{label}: empty metric list')
            seen = set()
            for m in r.get('metrics', []):
                name = m.get('metric')
                if not name or name in seen:
                    issues.append(f'{label}: missing or duplicated metric name')
                    continue
                seen.add(name)
                if not isinstance(m.get('n'), int) or m['n'] < 0:
                    issues.append(f'{label}/{name}: invalid n')
                value, status = m.get('value'), m.get('status')
                if value is None and (status != 'NOT MEASURED' or not m.get('reason')):
                    issues.append(f'{label}/{name}: unavailable metric lacks null/status/reason')
                elif value is not None and (status != 'MEASURED' or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    issues.append(f'{label}/{name}: measured metric invalid')
            checks.append({'agent': agent, 'run': number, 'rows': len(rows),
                           'metrics': len(r.get('metrics', [])), 'complete': len(issues) == before})
    # Inference source hashes must agree within a phase even when git HEAD differs
    # because evaluation-only commits were merged between specialists.
    fingerprints = {r.get('app_source_fingerprint') for a, s in sources.items()
                    if a in INFERENCE_AGENTS for r in select_runs(s, phase)}
    if len(fingerprints) > 1:
        issues.append('Specialists evaluated different application source hashes in this phase')
    return {'phase': phase, 'complete': not issues, 'dataset_fingerprint': frozen,
            'app_source_fingerprint': current, 'checks': checks, 'issues': issues}


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def sample(id: str, value: Any) -> dict | None:
    return {'id': str(id), 'value': float(value)} if finite(value) else None


def retrieval_samples(run: dict, name: str) -> list[dict] | None:
    parts = name.split('/')
    rows, config = run['per_question'], run['config']
    if len(parts) == 3 and '@' in parts[2]:
        group, variant, target = parts
        field, k_string = target.rsplit('@', 1)
        try:
            k = int(k_string)
        except ValueError:
            return None
        def included(row):
            return (group == 'all' or row.get('suite') == group or row.get('modality') == group or
                    (group == 'typo' and row.get('subset') == 'typo') or
                    (group == 'cross_modal' and row.get('type') == 'cross-modal'))
        selected = [r for r in rows if included(r)]
        values = []
        lookup = {r['id']: r for r in config.get('corpus_manifest', [])}
        for r in selected:
            ids = r.get('rankings', {}).get(variant, [])[:k]
            if field == 'returned_count':
                value = len(set(ids))
            elif field in {'unique_source_ratio', 'modality_entropy', 'gold_modality_hit'}:
                if not lookup:
                    return None
                if field == 'gold_modality_hit':
                    if not r['gold_ids']:
                        continue
                    gold = {lookup[i]['source_modality'] for i in r['gold_ids']}
                    value = float(any(lookup[i]['source_modality'] in gold for i in ids))
                else:
                    if not ids:
                        continue
                    if field == 'unique_source_ratio':
                        value = len({lookup[i]['source_id'] for i in ids}) / len(ids)
                    else:
                        counts = defaultdict(int)
                        for i in ids:
                            counts[lookup[i]['source_modality']] += 1
                        value = -sum((v/len(ids))*math.log2(v/len(ids)) for v in counts.values())
            else:
                if not r['gold_ids']:
                    continue
                value = r.get('metrics', {}).get(variant, {}).get(str(k), {}).get(field)
            point = sample(r['id'], value)
            if point:
                values.append(point)
        return values
    if len(parts) == 3 and parts[-1] == 'empty_candidate_rate':
        group, variant, _ = parts
        selected = [r for r in rows if r['unanswerable'] and
                    (group == 'all' or r.get('suite') == group or r.get('modality') == group or
                     (group == 'typo' and r.get('subset') == 'typo') or
                     (group == 'cross_modal' and r.get('type') == 'cross-modal'))]
        return [{'id': r['id'], 'value': float(not r['rankings'][variant])} for r in selected]
    robust = config.get('robustness', [])
    if name in {'cross_modal/source_page_hit@5', 'cross_modal/text_modality_hit@5'}:
        key = name.split('/')[1].split('@')[0]
        return [{'id': r['id'], 'value': r[key]} for r in robust if r.get('kind') == 'image-query']
    if name.startswith('degraded_scan/'):
        key = name.split('/')[1].split('@')[0]
        # Two probes from each derived page are related; the requested clustering
        # unit here is the authored question plus degradation, not independent runs.
        return [{'id': r['id'], 'value': r['metrics'][key]} for r in robust if r.get('kind') == 'degraded_scan']
    return None


def generation_samples(run: dict, name: str) -> list[dict] | None:
    target, _, modality = name.partition('__')
    rows = [r for r in run['per_question'] if not modality or r.get('modality') == modality]
    if target in {'abstention_precision', 'abstention_recall', 'false_refusal_rate', 'negative_answer_rate'}:
        if target == 'abstention_precision':
            return [{'id': r['id'], 'value': float(r['unanswerable'])} for r in rows if r['metrics']['abstained']]
        if target == 'false_refusal_rate':
            return [{'id': r['id'], 'value': float(r['metrics']['abstained'])} for r in rows if not r['unanswerable']]
        return [{'id': r['id'], 'value': float(r['metrics']['abstained']) if target == 'abstention_recall' else float(not r['metrics']['abstained'])}
                for r in rows if r['unanswerable']]
    if target in {'consistency_over_three_runs', 'three_run_pairwise_token_f1'}:
        key = 'three_way_exact' if target == 'consistency_over_three_runs' else 'pairwise_token_f1'
        return [{'id': r['id'], 'value': r[key]} for r in run.get('three_run_consistency_sample', [])]
    if target in {'generation_model_calls', 'verification_model_calls'}:
        return None  # Observed totals are descriptive, not mean-valued quality rates.
    values = [sample(r['id'], r['metrics'].get(target)) for r in rows if not r['unanswerable']]
    return [v for v in values if v is not None] if any(v is not None for v in values) else None


def metric_samples(agent: str, run: dict, metric: dict) -> tuple[list[dict] | None, str]:
    # Specialists may provide explicit statistical samples to preserve complicated
    # conditional denominators. They own these values and their definitions.
    explicit = run.get('statistic_samples', {}).get(metric['metric'])
    if explicit is not None:
        if isinstance(explicit, dict):
            estimator = explicit.get('estimator', explicit.get('aggregation', 'mean'))
            if estimator == 'quantile':
                estimator = {0.5: 'p50', 0.95: 'p95'}.get(explicit.get('quantile'), 'unsupported_quantile')
            return explicit.get('samples'), estimator
        return explicit, 'mean'
    if agent == 'retrieval-agent':
        return retrieval_samples(run, metric['metric']), 'mean'
    if agent == 'generation-agent':
        return generation_samples(run, metric['metric']), 'mean'
    return None, 'mean'


def bootstrap_interval(samples: list[list[dict]], estimator='mean', *, seed=SEED, draws=5000) -> dict:
    import numpy as np
    clusters = sorted({r['id'] for rows in samples for r in rows})
    if not clusters or any(not rows for rows in samples):
        return {'status': 'NOT MEASURED', 'reason': 'No applicable observations in at least one independent run.'}
    positions = {key: i for i, key in enumerate(clusters)}
    values = np.full((len(samples), len(clusters)), np.nan, dtype=float)
    for i, rows in enumerate(samples):
        if len({r['id'] for r in rows}) != len(rows):
            return {'status': 'NOT MEASURED', 'reason': 'Duplicate statistical sample IDs in a run; no independence assumption made.'}
        for r in rows:
            values[i, positions[r['id']]] = r['value']
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(clusters), size=(draws, len(clusters)))
    sampled = values[:, indices]
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        if estimator == 'mean':
            estimates = np.nanmean(sampled, axis=2)
        elif estimator in {'p50', 'p95'}:
            estimates = np.nanquantile(sampled, .5 if estimator == 'p50' else .95, axis=2, method='linear')
        else:
            return {'status': 'NOT MEASURED', 'reason': f'Unsupported bootstrap estimator: {estimator}'}
        # Equal weight to independently run scorecards. The same sampled question
        # indices apply to both runs; repeated inference is not a new question.
        estimates = np.mean(estimates, axis=0)
    estimates = estimates[np.isfinite(estimates)]
    if not len(estimates):
        return {'status': 'NOT MEASURED', 'reason': 'No finite bootstrap resamples.'}
    low, high = np.quantile(estimates, [.025, .975], method='linear')
    return {'status': 'MEASURED', 'low': float(low), 'high': float(high),
            'level': .95, 'method': 'Percentile bootstrap; question/probe ID clusters shared across independent runs',
            'estimator': estimator, 'draws': draws, 'valid_draws': len(estimates), 'seed': seed,
            'n_clusters': len(clusters), 'n_observations': sum(len(rows) for rows in samples),
            'small_sample_note': ('A degenerate empirical bootstrap interval does not establish a population guarantee, including when no failures were observed.'
                                  if math.isclose(float(low), float(high), abs_tol=1e-15) else
                                  'Few probes provide weak population evidence.' if len(clusters) < 10 else None)}


def estimate(samples: list[dict], estimator: str) -> float:
    import numpy as np
    values = [row['value'] for row in samples]
    if estimator == 'mean':
        return statistics.mean(values)
    return float(np.quantile(values, .5 if estimator == 'p50' else .95, method='linear'))


def aggregate_metrics(sources: dict, phase: str, draws=5000) -> list[dict]:
    output, ci_cache = [], {}
    for agent in INFERENCE_AGENTS:
        runs = select_runs(sources[agent], phase)
        names = sorted({m['metric'] for r in runs for m in r['metrics']})
        lookup = [{m['metric']: m for m in r['metrics']} for r in runs]
        for name in names:
            points = [items.get(name) for items in lookup]
            row = {'agent': agent, 'metric': name, 'run_values': [p.get('value') if p else None for p in points],
                   'n_per_run': [p.get('n') if p else 0 for p in points], 'n_runs': len(runs),
                   'status': 'MEASURED', 'value': None, 'variance_between_runs': None,
                   'standard_deviation_between_runs': None, 'absolute_run_difference': None,
                   'metric_metadata_per_run': [{k: v for k, v in p.items() if k not in {'metric', 'value', 'n', 'status', 'reason'}}
                                               if p else {} for p in points]}
            if agent == 'generation-agent' and name in {'consistency_over_three_runs', 'three_run_pairwise_token_f1'}:
                # This is one cross-run statistic over three real passes, stored
                # after run 2 completes, not a pair of independent scorecards.
                observed = [(r, p) for r, p in zip(runs, points) if p and p.get('value') is not None]
                if len(observed) == 1:
                    observed_run, observed_point = observed[0]
                    values_for_ci = generation_samples(observed_run, name)
                    if values_for_ci and len(values_for_ci) == observed_point['n'] and math.isclose(
                            estimate(values_for_ci, 'mean'), observed_point['value'], rel_tol=1e-8, abs_tol=1e-9):
                        row.update(value=observed_point['value'], reason=None,
                                   statistic_scope='One three-pass consistency statistic on the predeclared five-question sample; not a two-run mean.',
                                   independent_inference_passes=3,
                                   ci95=bootstrap_interval([values_for_ci], draws=draws),
                                   n_clusters=len(values_for_ci), n_observations=len(values_for_ci))
                        output.append(row)
                        continue
            if any(p is None or p.get('value') is None for p in points):
                row.update(status='NOT MEASURED', reason='; '.join(dict.fromkeys(
                    p.get('reason') or 'No reason provided' if p else 'Metric absent from one run' for p in points
                    if p is None or p.get('value') is None)),
                    ci95={'status': 'NOT MEASURED', 'reason': 'Metric unavailable in at least one required run.'})
                output.append(row)
                continue
            values = [p['value'] for p in points]
            row.update(value=statistics.mean(values), reason=None,
                       variance_between_runs=statistics.variance(values) if len(values) > 1 else None,
                       standard_deviation_between_runs=statistics.stdev(values) if len(values) > 1 else None,
                       absolute_run_difference=abs(values[1]-values[0]) if len(values) == 2 else None)
            samples, estimators = zip(*(metric_samples(agent, run, point) for run, point in zip(runs, points)))
            invalid = None
            if any(s is None for s in samples):
                invalid = 'Raw samples/estimator mapping unavailable or metric is a descriptive total; no interval invented.'
            elif len(set(estimators)) != 1:
                invalid = 'Estimator differs between independent runs.'
            else:
                for s, p, estimator in zip(samples, points, estimators):
                    if len(s) != p['n']:
                        invalid = 'Raw sample count differs from published denominator; specialist clarification required.'
                        break
                    if not s or not math.isclose(estimate(s, estimator), p['value'], rel_tol=1e-8, abs_tol=1e-9):
                        invalid = 'Raw sample estimator does not reproduce published point; no interval invented.'
                        break
            if invalid:
                row['ci95'] = {'status': 'NOT MEASURED', 'reason': invalid}
            else:
                key = digest([samples, estimators[0], draws])
                if key not in ci_cache:
                    ci_cache[key] = bootstrap_interval(list(samples), estimators[0], draws=draws)
                row['ci95'] = ci_cache[key]
                row['n_clusters'] = row['ci95'].get('n_clusters')
                row['n_observations'] = row['ci95'].get('n_observations')
            output.append(row)
    return output


def paired_significance(sources: dict, phase: str, permutations=20000, draws=5000) -> list[dict]:
    import numpy as np
    runs = select_runs(sources['retrieval-agent'], phase)
    tests = []
    for subset in ['all', 'typo']:
        for field in ['precision', 'recall', 'mrr', 'ndcg']:
            k = 5
            def values(variant):
                grouped = defaultdict(list)
                for run in runs:
                    for r in run['per_question']:
                        if r['gold_ids'] and (subset == 'all' or r.get('subset') == 'typo'):
                            grouped[r['id']].append(float(r['metrics'][variant][str(k)][field]))
                return {id: statistics.mean(v) for id, v in grouped.items()}
            singles = {channel: values(channel) for channel in ['dense', 'word', 'fuzzy']}
            best = max(singles, key=lambda channel: statistics.mean(singles[channel].values()))
            h, b = values('hybrid_runtime'), singles[best]
            ids = sorted(set(h) & set(b))
            diff = np.array([h[id]-b[id] for id in ids])
            observed = float(np.mean(diff))
            nonzero = diff[np.abs(diff) > 1e-14]
            if not len(nonzero):
                p, method, actual = 1.0, 'Exact paired sign permutation (all differences zero)', 1
            elif len(nonzero) <= 16:
                outcomes = np.array([sum(d*s for d, s in zip(nonzero, signs))/len(diff)
                                     for signs in itertools.product([-1, 1], repeat=len(nonzero))])
                p = float(np.mean(np.abs(outcomes) >= abs(observed)-1e-14))
                method, actual = 'Exact paired two-sided sign permutation', len(outcomes)
            else:
                rng = np.random.default_rng(SEED)
                outcomes = (rng.choice([-1, 1], size=(permutations, len(diff))) * diff).mean(axis=1)
                p = float((1+np.sum(np.abs(outcomes) >= abs(observed)-1e-14))/(permutations+1))
                method, actual = 'Monte Carlo paired two-sided sign permutation; plus-one correction', permutations
            ci = bootstrap_interval([[{'id': id, 'value': float(d)} for id, d in zip(ids, diff)]], draws=draws)
            tests.append({'metric': f'{subset}/hybrid_runtime-vs-best-single/{field}@{k}',
                          'subset': subset, 'measure': field, 'k': k, 'n': len(ids), 'n_runs': len(runs),
                          'hybrid_mean': statistics.mean(h.values()), 'best_single': best,
                          'best_single_mean': statistics.mean(b.values()), 'difference': observed,
                          'ci95_difference': ci, 'p_value_two_sided': p, 'test': method,
                          'permutations': actual, 'seed': SEED,
                          'selection_note': 'Best single selected on these observed test questions, separately per metric/subset. Exploratory comparison; no held-out selection or superiority guarantee.',
                          'paired_differences': [{'id': id, 'value': float(d)} for id, d in zip(ids, diff)]})
    # Holm correction across the eight disclosed exploratory comparisons.
    order = sorted(range(len(tests)), key=lambda i: tests[i]['p_value_two_sided'])
    previous = 0.0
    for rank, i in enumerate(order):
        previous = max(previous, min(1., tests[i]['p_value_two_sided']*(len(tests)-rank)))
        tests[i]['p_value_holm'] = previous
        tests[i]['multiplicity_family_n'] = len(tests)
        tests[i]['hybrid_significantly_better_at_05'] = previous < .05 and tests[i]['difference'] > 0
    return tests


def atomic_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def source_provenance(sources: dict, phase: str) -> list[dict]:
    return [{'agent': agent, 'file': 'results/' + agent + '.json',
             'runs': [{'run': r['run'], 'run_id': r['run_id'], 'result_sha256': digest(r),
                       'timestamp_utc': r['timestamp_utc'], 'app_commit': r['app_commit'],
                       'app_source_fingerprint': r['app_source_fingerprint'], 'models': r.get('models', {})}
                      for r in select_runs(source, 'baseline' if agent == 'testset-agent' else phase)]}
            for agent, source in sorted(sources.items())]


def measurement_code_manifest(app: Path) -> dict:
    """Pin the assembled metric implementation before any application fixes.

    Formatting/docs are excluded so a report typo can be corrected without
    changing measurement code. This is the assembly-time code manifest; older
    specialist processes do not retroactively acquire a code hash.
    """
    root = app / 'evaluation'
    paths = sorted({p for pattern in ['*.py', '*.mjs', 'requirements*.txt'] for p in root.glob(pattern)
                    if p.name != 'stats_report.py'})
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    return {'fingerprint': digest(files), 'files': files,
            'scope': 'Assembly-time evaluator/metric/dependency files; report formatting excluded.'}


def aggregate(results_dir: Path, overrides: dict, phase: str, app: Path, evaluation: Path,
              *, bootstrap_samples=5000, permutations=20000) -> bool:
    sources = load_sources(results_dir, overrides)
    status = assess_completeness(sources, phase, app)
    if not status['complete']:
        # This is an explicitly partial status artifact, never the frozen baseline.
        atomic_json(evaluation / 'runtime/stats-completeness.json', status)
        print(json.dumps(status, indent=2))
        return False
    provenance = source_provenance(sources, phase)
    code = measurement_code_manifest(app)
    if phase == 'final':
        baseline_path = evaluation / 'baseline_results.json'
        if not baseline_path.is_file():
            raise RuntimeError('A complete frozen baseline is required before final statistical assembly.')
        baseline = json.loads(baseline_path.read_text())
        if baseline.get('dataset_fingerprint') != status['dataset_fingerprint']:
            raise RuntimeError('Final dataset differs from the frozen baseline.')
        if baseline.get('measurement_code', {}).get('fingerprint') != code['fingerprint']:
            raise RuntimeError('Evaluation metric code/dependencies differ from the frozen baseline; refusing a before/after comparison.')
    snapshot_path = evaluation / (phase + '_results.json')
    if snapshot_path.exists():
        old = json.loads(snapshot_path.read_text())
        if old.get('sources') != provenance:
            raise RuntimeError(f'{snapshot_path.name} already frozen with different raw observations; refusing to overwrite.')
        payload = old
    else:
        payload = {'schema_version': 1, 'phase': phase, 'complete': True,
                   'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
                   'dataset_fingerprint': status['dataset_fingerprint'],
                   'app_source_fingerprint': status['app_source_fingerprint'],
                   'measurement_code': code,
                   'sources': provenance, 'completeness': status,
                   'aggregation': 'Equal mean of two independent scorecards. CI resamples question/probe IDs jointly across runs, never counts repeats as independent questions.',
                   'bootstrap_samples': bootstrap_samples, 'permutations': permutations,
                   'metrics': aggregate_metrics(sources, phase, bootstrap_samples),
                   'paired_significance': paired_significance(sources, phase, permutations, bootstrap_samples)}
        atomic_json(snapshot_path, payload)
    from stats_report import write_outputs
    write_outputs(evaluation, payload)
    # The stats agent's own result is a provenance-linked summary, not fabricated
    # independent measurements of specialist outputs.
    stats_path = evaluation / 'results/stats-agent.json'
    old_stats = json.loads(stats_path.read_text()) if stats_path.exists() else {'schema_version': 1, 'agent': 'stats-agent', 'runs': []}
    old_stats['runs'] = [r for r in old_stats['runs'] if r.get('phase') != phase]
    old_stats['runs'].append({'phase': phase, 'run': 1, 'run_id': phase+'-statistical-assembly',
                             'timestamp_utc': payload['timestamp_utc'], 'seed': SEED,
                             'dataset_fingerprint': payload['dataset_fingerprint'],
                             'app_source_fingerprint': payload['app_source_fingerprint'],
                             'config': {'inference_performed_by_stats_agent': False, 'bootstrap_samples': payload['bootstrap_samples'],
                                        'independent_inference_runs_per_specialist': 2},
                             'metrics': [{'metric': t['metric'], 'value': t['difference'], 'n': t['n'],
                                          'status': 'MEASURED', 'reason': None, 'ci95': t['ci95_difference'],
                                          'p_value_holm': t['p_value_holm']} for t in payload['paired_significance']],
                             'per_question': payload['paired_significance']})
    atomic_json(stats_path, old_stats)
    print(json.dumps({'event': 'snapshot_frozen', 'phase': phase, 'file': snapshot_path.name,
                      'metrics': len(payload['metrics']), 'paired_tests': len(payload['paired_significance'])}))
    return True
