#!/usr/bin/env python3
"""Dispatch the frozen, independent specialist evaluation and assemble its scorecard.

No application imports occur here. A normal run executes real specialist runners;
--aggregate-only reads their observations and never claims to repeat inference.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

EVALUATION = Path(__file__).resolve().parent
APP = EVALUATION.parent
GROUPS = {
    'ingestion': ('ingestion_eval.py', 'ingestion-agent.json'),
    'retrieval': ('retrieval_eval.py', 'retrieval-agent.json'),
    'generation': ('generation_eval.py', 'generation-agent.json'),
    'homeatlas': ('homeatlas_eval.py', 'homeatlas-agent.json'),
    'security': ('security_system_eval.py', 'security-system-agent.json'),
}
GROUP_ALIASES = {
    'A': 'retrieval', 'B': 'generation', 'C': 'generation', 'D': 'generation',
    'E': 'homeatlas', 'F': 'ingestion', 'G': 'retrieval', 'H': 'homeatlas',
    'I': 'homeatlas', 'J': 'security', 'K': 'security', 'L': 'stats',
    'security-system': 'security',
}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--group', action='append', help='Group name or A-L; repeat or comma-separate. Default: all.')
    p.add_argument('--phase', choices=['baseline', 'final'], default='baseline')
    p.add_argument('--run', choices=['1', '2', 'both'], default='both', help='Default: both independent passes.')
    p.add_argument('--results-dir', type=Path, default=EVALUATION / 'results')
    p.add_argument('--result', action='append', default=[], metavar='AGENT=PATH', help='Read-only result override for aggregation/checks.')
    p.add_argument('--app-root', type=Path, default=Path(os.environ.get('EVAL_APP_ROOT', APP)))
    p.add_argument('--python', dest='python_executable', help='Specialist Python interpreter; otherwise EVAL_PYTHON, isolated venv, or current Python.')
    p.add_argument('--aggregate-only', action='store_true', help='Validate and summarize existing real runs; do not run inference.')
    p.add_argument('--check', action='store_true', help='Read-only preflight and result-completeness check.')
    p.add_argument('--dry-run', action='store_true', help='Print command plan without executing specialists or freezing results.')
    p.add_argument('--bootstrap-samples', type=int, default=5000)
    p.add_argument('--permutations', type=int, default=20000)
    return p


def selected_groups(values):
    if not values:
        return list(GROUPS)
    selected = []
    for value in values:
        for token in value.split(','):
            token = token.strip()
            name = GROUP_ALIASES.get(token, token.lower())
            if name == 'all':
                selected.extend(GROUPS)
            elif name in GROUPS or name == 'stats':
                selected.append(name)
            else:
                raise ValueError(f'Unknown evaluation group: {token}')
    return list(dict.fromkeys(selected))


def interpreter(args):
    if args.python_executable or os.environ.get('EVAL_PYTHON'):
        return args.python_executable or os.environ['EVAL_PYTHON']
    local = args.app_root.resolve() / 'evaluation/.venv/bin/python'
    return str(local) if local.exists() else sys.executable


def command_plan(args, groups):
    commands = []
    runs = [1, 2] if args.run == 'both' else [int(args.run)]
    # Model-heavy evaluations are deliberately sequential on a development host.
    # Security runs last because stage metrics reuse the same completed generation pass.
    for run in runs:
        for group in GROUPS:
            if group not in groups:
                continue
            script, filename = GROUPS[group]
            commands.append((group, run, [interpreter(args), str(EVALUATION / script),
                             '--phase', args.phase, '--run', str(run),
                             '--output', str(args.results_dir.resolve() / filename)]))
    return commands


def result_overrides(values):
    out = {}
    for value in values:
        if '=' not in value:
            raise ValueError('--result requires AGENT=PATH')
        agent, path = value.split('=', 1)
        agent = GROUP_ALIASES.get(agent, agent)
        if agent in GROUPS:
            agent = GROUPS[agent][1].removesuffix('.json')
        out[agent] = Path(path).resolve()
    return out


def main():
    args = parser().parse_args()
    try:
        groups = selected_groups(args.group)
        overrides = result_overrides(args.result)
    except ValueError as error:
        parser().error(str(error))
    if args.bootstrap_samples < 100 or args.permutations < 100:
        parser().error('Use at least 100 bootstrap samples and permutations.')
    app = args.app_root.resolve()
    os.environ.setdefault('EVAL_APP_ROOT', str(app))
    os.environ.setdefault('EVAL_SHARED_RUNTIME', str(app / 'evaluation/runtime'))
    os.environ.setdefault('MODEL_DIR', str(app / 'data/models'))
    os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
    os.environ.setdefault('RAGAS_DO_NOT_TRACK', 'true')
    os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')
    plan = command_plan(args, groups)
    if args.dry_run:
        print(json.dumps({'phase': args.phase, 'runs': args.run,
                          'commands': [{'group': g, 'run': r, 'argv': cmd} for g, r, cmd in plan],
                          'aggregate_requires': 'Frozen input audit and two complete passes from every specialist.'}, indent=2))
        return 0
    chosen_python = interpreter(args)
    # Aggregation also needs the pinned numerical environment, not merely child
    # inference processes. Preserve --help/--dry-run as standard-library-only.
    import shutil
    chosen_path = Path(shutil.which(chosen_python) or chosen_python).absolute()
    if Path(sys.executable).absolute() != chosen_path:
        os.execv(str(chosen_path), [str(chosen_path), str(Path(__file__).resolve()), *sys.argv[1:]])
    from protocol import frozen_dataset, app_fingerprint
    frozen_dataset()  # Fail before any upload or model call if supplied gold changed.
    if not args.aggregate_only and not args.check:
        # Specialist import roots differ. Isolated worktrees are supported only
        # when their application source matches the requested live app root.
        if app_fingerprint(APP)['app_source_fingerprint'] != app_fingerprint(app)['app_source_fingerprint']:
            raise SystemExit('Evaluator checkout and --app-root application source hashes differ. Apply the same application commit to both before dispatch; no inference was started.')
    missing = [str(Path(cmd[1]).relative_to(EVALUATION)) for _, _, cmd in plan if not Path(cmd[1]).is_file()]
    if missing and not args.aggregate_only and not args.check:
        raise SystemExit('Missing specialist scripts: ' + ', '.join(sorted(set(missing))))
    if args.check:
        from stats_analysis import assess_completeness, load_sources
        sources = load_sources(args.results_dir, overrides)
        status = assess_completeness(sources, args.phase, app)
        print(json.dumps(status, indent=2))
        return 0 if status['complete'] else 2
    if not args.aggregate_only:
        for group, run, command in plan:
            print(json.dumps({'event': 'specialist_start', 'group': group, 'phase': args.phase, 'run': run}), flush=True)
            subprocess.run(command, cwd=app, env=os.environ.copy(), check=True)
    # A selected group run is useful on its own; a partial suite never freezes a baseline.
    from stats_analysis import aggregate
    complete = aggregate(args.results_dir, overrides, args.phase, app, EVALUATION,
                         bootstrap_samples=args.bootstrap_samples, permutations=args.permutations)
    if not complete:
        print('Suite incomplete: no baseline/final snapshot written. Specialist observations are preserved.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
