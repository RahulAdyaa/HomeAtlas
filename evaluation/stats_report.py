"""Render audit-friendly reports exclusively from frozen aggregated observations."""
from __future__ import annotations
import csv
import json
from pathlib import Path


def number(value):
    return 'NOT MEASURED' if value is None else format(value, '.6g')


def text(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def estimate_cell(row):
    if row is None:
        return 'No completed phase'
    n = '/'.join(str(v) for v in row.get('n_per_run', []))
    if row['value'] is None:
        return f'NOT MEASURED (n={n}; {text(row.get("reason"))})'
    ci = row.get('ci95', {})
    if ci.get('status') == 'MEASURED':
        interval = f'95% CI [{number(ci["low"])}, {number(ci["high"])}]'
        count = f'n={ci["n_clusters"]} clusters; observations={ci["n_observations"]}'
        if ci.get('low') == ci.get('high'):
            interval += '; degenerate empirical interval'
    else:
        interval = 'CI NOT MEASURED'
        count = f'n/run={n}'
    return f'{number(row["value"])} ({interval}; {count})'


def table(rows, baseline=None):
    lines = ['| Metric | Baseline: two-run mean, CI and n | Final: two-run mean, CI and n | Run SD (baseline / final) |',
             '| --- | --- | --- | --- |']
    for row in rows:
        key = (row['agent'], row['metric'])
        b = baseline.get(key) if baseline is not None else row
        f = row if baseline is not None else None
        lines.append(f'| `{text(row["metric"])}` | {estimate_cell(b)} | {estimate_cell(f)} | {number(b.get("standard_deviation_between_runs")) if b else "—"} / {number(f.get("standard_deviation_between_runs")) if f else "—"} |')
    return lines


def write_csv(path: Path, baseline, final):
    fields = ['phase', 'agent', 'metric', 'status', 'value', 'run_1_value', 'run_2_value',
              'n_run_1', 'n_run_2', 'n_clusters', 'n_observations', 'ci95_low', 'ci95_high',
              'ci95_status', 'ci95_reason', 'variance_between_runs', 'standard_deviation_between_runs',
              'absolute_run_difference', 'reason']
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for payload in [baseline, final]:
            if not payload:
                continue
            for m in payload['metrics']:
                ci = m.get('ci95', {})
                writer.writerow({'phase': payload['phase'], 'agent': m['agent'], 'metric': m['metric'],
                                 'status': m['status'], 'value': m.get('value'),
                                 'run_1_value': m['run_values'][0], 'run_2_value': m['run_values'][1],
                                 'n_run_1': m['n_per_run'][0], 'n_run_2': m['n_per_run'][1],
                                 'n_clusters': m.get('n_clusters'), 'n_observations': m.get('n_observations'),
                                 'ci95_low': ci.get('low'), 'ci95_high': ci.get('high'),
                                 'ci95_status': ci.get('status'), 'ci95_reason': ci.get('reason'),
                                 'variance_between_runs': m.get('variance_between_runs'),
                                 'standard_deviation_between_runs': m.get('standard_deviation_between_runs'),
                                 'absolute_run_difference': m.get('absolute_run_difference'), 'reason': m.get('reason')})


def write_outputs(evaluation: Path, payload: dict):
    baseline_path, final_path = evaluation / 'baseline_results.json', evaluation / 'final_results.json'
    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else None
    final = json.loads(final_path.read_text()) if final_path.exists() else None
    current = final or baseline or payload
    baseline_lookup = {(m['agent'], m['metric']): m for m in baseline['metrics']} if final and baseline else None
    all_metrics = current['metrics']
    write_csv(evaluation / 'stats-metric-scorecard.csv', baseline, final)
    lines = ['# HomeAtlas multimodal RAG evaluation', '',
             f'Completed phase: **{current["phase"]}**. Assembly timestamp: `{current["timestamp_utc"]}`. '
             'All values below are generated from specialist result files. Missing measurements remain null with reasons.', '',
             '## Frozen scope and provenance', '',
             'The frozen corpus contains 5 original synthetic CC0 PDFs (20 pages), 60 PDF questions, '
             '20 fictional household documents and 78 household questions: 138 questions in total. '
             'The retrieval suite has 121 answerable questions and 17 negatives; the generation suite has '
             '50 answerable PDF questions and 10 negatives. Supplemental upload, cache, security and '
             'degraded-image probes report their own denominators. These suites are not interchangeable.', '',
             f'- Dataset fingerprint: `{current["dataset_fingerprint"]}`.',
             f'- App source fingerprint: `{current["app_source_fingerprint"]}`.',
             '- Judge model: **NOT MEASURED — no free-tier judge credential was configured**. '
             'Local generation is not an independent judge. No paid fallback was used.',
             '- Each inference specialist ran two actual independent passes. A generation response from run 1 '
             'cannot satisfy run 2; run-scoped resumability is distinct from a new inference pass.',
             '- Source hashes, model revisions, timestamps and raw run digests are retained in '
             '[baseline_results.json](baseline_results.json)' + (' and [final_results.json](final_results.json).' if final else '. Final application evaluation is not complete yet.'), '',
             '| Specialist | Run | Application commit | Timestamp UTC |', '| --- | --- | --- | --- |']
    for source in current['sources']:
        for run in source['runs']:
            lines.append(f'| {source["agent"]} | {run["run"]} | `{run["app_commit"]}` | {run["timestamp_utc"]} |')
    lines += ['', 'Evaluation-only commits can differ between specialists; the application source hash is authoritative. '
              'The input audit runs once because it checks immutable files rather than performing model inference.', '',
              '## Statistical method', '',
              f'Point estimates are equal means of the two independent per-run scorecards. The 95% percentile bootstrap '
              f'uses {current["bootstrap_samples"]} resamples and seed {current["seed"]}. '
              'Question/probe IDs are resampled jointly across repeated runs, so two observations of one question '
              'do not become two independent questions. Sample standard deviation uses the two run scores '
              '(denominator runs − 1). Intervals describe this small synthetic question distribution, not a guarantee '
              'about real household documents. A one-probe degenerate interval is explicitly weak evidence.', '',
              'A confidence interval is computed only if raw sample counts and the specified estimator reproduce '
              'both published point estimates. Otherwise its status and reason appear in the complete scorecard. '
              'Descriptive totals, extrema, missing numeric confidences and unsupported estimators are never '
              'assigned invented intervals. A zero-failure sample can produce a degenerate [0,0] bootstrap '
              'interval; it does not prove a zero population failure rate. In particular, zero false hits '
              'on the ten near-miss probes cannot establish the requested population rate below 2%. '
              'Repeated runs of those same probes do not double the number of independent probes. '
              'Conditional denominators (for example, answers containing citations) '
              'are retained. Every metric and its n/run, run variance, interval status and reason is in '
              '[stats-metric-scorecard.csv](stats-metric-scorecard.csv).', '',
              '### Paired hybrid versus strongest single channel', '',
              'The strongest dense/word/fuzzy channel is selected on these observed questions, separately for '
              'each measure and subset. These are exploratory comparisons, not held-out model selection. '
              'Paired two-sided sign permutation uses question-averaged run scores; exact enumeration is used '
              'when feasible, otherwise seeded Monte Carlo with a plus-one correction. Holm correction covers '
              'all eight displayed tests. Positive difference favors runtime hybrid.', '',
              '| Phase | Subset | Measure @5 | n | Best single | Hybrid | Single | Difference [95% CI] | p (two-sided) | p (Holm) |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for phase_payload in [baseline, final]:
        if not phase_payload:
            continue
        for t in phase_payload['paired_significance']:
            ci = t['ci95_difference']
            lines.append(f'| {phase_payload["phase"]} | {t["subset"]} | {t["measure"]} | {t["n"]} | {t["best_single"]} | '
                         f'{number(t["hybrid_mean"])} | {number(t["best_single_mean"])} | {number(t["difference"])} '
                         f'[{number(ci.get("low"))}, {number(ci.get("high"))}] | {number(t["p_value_two_sided"])} | {number(t["p_value_holm"])} |')
    typo = [t for t in current['paired_significance'] if t['subset'] == 'typo']
    all_better = all(t['difference'] > 0 for t in typo)
    lines += ['', ('Hybrid exceeds the strongest single channel on every displayed typo measure.' if all_better else
                   '**The target “hybrid beats every single channel on the typo subset” is not met.** '
                   'The table retains measures where the strongest single channel ties or outperforms hybrid. '
                   'Ranks and per-question paired differences remain available for diagnosis.'), '',
              '## A/G: retrieval, typo robustness and cross-modal search', '',
              'Runtime output is capped at 5; diagnostic top-10 runs are explicitly named. Precision divides by '
              'requested K even if fewer results return. AP@K divides by total relevant chunks; R-Precision@K '
              'uses the first min(K,R) results divided by R. Frozen PDF gold marks all chunks on an authored '
              'relevant page, so fixed-K chunk recall has a ceiling on pages with many OCR chunks. A page hit '
              'does not establish that the answer facts were extracted. Source-page and literal evidence '
              'diagnostics are reported separately.', '',
              '### Channel comparison and K=1/3/5/10', '']
    if any(t['measure'] == 'mrr' and t['best_single_mean'] >= 1 for t in typo):
        lines += ['The strongest single channel already achieves the maximum MRR on this typo sample. '
                  'Strictly beating that value is impossible on the same fixed sample; tying it still does '
                  'not satisfy the requested strict-superiority target.', '']
    selected = [m for m in all_metrics if m['agent'] == 'retrieval-agent' and
                m['metric'].split('/')[0] in {'all', 'typo'} and
                len(m['metric'].split('/')) == 3 and m['metric'].split('/')[1] in
                {'dense', 'word', 'fuzzy', 'hybrid_runtime', 'hybrid_text_diagnostic10'} and
                m['metric'].split('/')[2].split('@')[0] in {'precision', 'recall', 'f1', 'hit', 'mrr', 'ndcg', 'map', 'r_precision'}]
    lines += table(selected, baseline_lookup)
    lines += ['', '### Per-modality runtime results', '']
    selected = [m for m in all_metrics if m['agent'] == 'retrieval-agent' and
                len(m['metric'].split('/')) == 3 and m['metric'].split('/')[0] in {'text', 'table', 'image', 'chart', 'scanned', 'household'} and
                m['metric'].split('/')[1] == 'hybrid_runtime' and m['metric'].endswith('@5')]
    lines += table(selected, baseline_lookup)
    lines += ['', '### RRF sensitivity, optional reranker and robustness', '',
              'Sensitivity tests use RRF k=10/30/60/100. Configured channel weights are all equal to 1, '
              'so “configured” and “equal” weighted experiments coincide by design; this is not evidence '
              'that arbitrary unequal weights are equivalent. The optional reranker is evaluated rather '
              'than assumed beneficial. All settings and K values remain in the complete CSV and raw results.', '']
    selected = [m for m in all_metrics if m['agent'] == 'retrieval-agent' and
                ((m['metric'].startswith(('all/rrf_', 'typo/rrf_', 'all/reranked_', 'typo/reranked_')) and
                  m['metric'].split('/')[-1] in {'recall@5', 'mrr@5', 'ndcg@5'}) or
                 m['metric'].startswith(('cross_modal/', 'degraded_scan/', 'paraphrase/', 'typo/pairwise_')) or
                 (m['metric'].startswith('all/hybrid_runtime/') and m['metric'].split('/')[-1].split('@')[0] in {'unique_source_ratio', 'modality_entropy', 'gold_modality_hit'}))]
    lines += table(selected, baseline_lookup)
    privacy_rows = [(phase_payload['phase'], m) for phase_payload in [baseline, final] if phase_payload
                    for m in phase_payload['metrics'] if m['metric'] == 'sensitive_answer_cache_persistence_rate']
    if privacy_rows:
        lines += ['', '### Strict cache privacy gap', '']
        for observed_phase, m in privacy_rows:
            finding = ('The requested zero-sensitive-content cache target is **NOT MET**.' if m['value'] is not None and m['value'] > 0 else
                       'No persistence was observed in this small synthetic sample; this does not establish a zero population leakage rate.' if m['value'] == 0 else
                       'Sensitive-content cache persistence is NOT MEASURED for this phase.')
            lines.append(observed_phase.capitalize() + ' sensitive-answer canary persistence: ' + estimate_cell(m) +
                         '. ' + finding + ' '
                         'Household/user isolation is a separate check and does not remove this persistence. '
                         'Private process-log leakage remains NOT MEASURED; no real private logs were inspected.')
    chapters = [
        ('B/C/D: generation, citations and abstention', 'generation-agent',
         'Exact match, token F1 and ROUGE-L compare reference wording and can penalize valid longer answers. '
         'Custom E5 BERTScore is token alignment using the pinned multilingual embedding encoder, not the '
         'standard English BERTScore benchmark. Gold citation scores check authored chunk/page gold and '
         'exact canonical quotation; they are not independent per-claim faithfulness scores. Literal term '
         'coverage and answer/reference length ratio are diagnostics, not semantic correctness/completeness. '
         'Three-run consistency is a predeclared five-question sample, distinct from the two full 60-question passes.'),
        ('E/H/I: household locations, freshness, cache and calibration', 'homeatlas-agent',
         'Uploaded-document Q/A fact presence is distinct from automatic structured entity extraction. '
         'Cache hit rate and cached-answer correctness are separate measurements. Generated-answer call '
         'savings are measured on a separate instrumented pair, not inferred from saved inventory fields. '
         'Room/zone/container and full-path denominators differ; only one container case is available. '
         'The current endpoint has no effective follow-up history support. Categorical confidence cannot '
         'be used as a numeric correctness probability for AUROC, Brier, ECE or reliability bins.'),
        ('F: ingestion, OCR, tables, visual evidence and chunking', 'ingestion-agent',
         'OCR uses authored page transcripts. Literal table-cell presence and flattened row sequence '
         'are not structured table extraction or TEDS. Image labels and chart numerals are text extraction '
         'diagnostics, not chart reasoning, semantic figure detection, captions or hallucination judgment. '
         'Parser timing excludes upload, queueing, embeddings and database publication.'),
        ('J/K: isolation, injection resistance and system measurements', 'security-system-agent',
         'Disposable authenticated accounts are used; no real household documents are evaluated. '
         'Authorized query/answer content intentionally persists in a household-and-user-scoped cache; '
         'this is not a claim of zero sensitive content in cache. Process logs containing possible private '
         'activity were not read. Small concurrent saved-fact probes do not establish full multimodal '
         'generation capacity. Local inference has no per-token invoice, but total hardware/energy cost '
         'was not measured. Shared-machine model contention and lock waiting are distinguished where '
         'instrumented; before/after latency differences are observational, not causal speed claims.'),
    ]
    for heading, agent, note in chapters:
        lines += ['', '## ' + heading, '', note, '']
        selected = [m for m in all_metrics if m['agent'] == agent]
        lines += table(selected, baseline_lookup)
    lines += ['', '## Limitations and interpretation', '',
              '- All documents, identifiers, names and account fixtures are synthetic. This benchmark does '
              'not establish accuracy for private identity cards, multilingual handwriting, arbitrary spreadsheets '
              'or unseen household layouts.',
              '- Related typo variants and questions from the same small document set limit generalization. '
              'The bootstrap clusters repeated runs by question ID; it does not turn the corpus into a '
              'representative population sample or account for every higher-level document dependency.',
              '- With no independent free-tier judge, faithfulness, semantic answer correctness, claim '
              'grounding, multimodal judgment and hallucination rates remain NOT MEASURED. A matching '
              'number or an exact source quote does not prove a full answer is correct.',
              '- Numeric trust probabilities, structured table output, dedicated semantic figure detection '
              'and image captioning are absent or unmeasured capabilities as identified in each row. '
              'The report never substitutes a lexical heuristic under those metric names.',
              '- Browser citation click-through, isolated 3D rendering FPS and view-ready time are '
              'NOT MEASURED unless an actual supported browser experiment is supplied. A render loop '
              'callback or a valid citation URL alone does not establish those results.',
              '- Complete run variance is retained. Identical deterministic rankings can produce zero '
              'run variance while host load changes timing. No threshold, frozen question or failing '
              'case was removed to raise scores.', '',
              '## Reproduce and audit', '',
              'See [evaluation setup](README.md). The default command dispatches actual specialist '
              'runs twice; aggregation alone reads results and does not replay inference.', '',
              '```sh', 'python evaluation/run_eval.py',
              'python evaluation/run_eval.py --phase final',
              'python evaluation/run_eval.py --group retrieval --phase final',
              'python evaluation/run_eval.py --aggregate-only --phase final', '```', '',
              '[Complete metric scorecard](stats-metric-scorecard.csv) · '
              '[Frozen input contract](CONTRACT.md) · [Specialist raw results](results/) · '
              '[Fix log](CHANGELOG.md)', '']
    (evaluation / 'RAG_EVALUATION_REPORT.md').write_text('\n'.join(lines))
