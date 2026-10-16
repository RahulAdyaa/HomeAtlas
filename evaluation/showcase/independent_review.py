#!/usr/bin/env python3
"""Mechanically aggregate existing Codex judgments; no answers are judged here.

Only saved final-run-01 rows and the three explicitly supplied independent reviews
are inputs. Nulls remain null, authored negatives remain separate, and original
measurement outputs are never modified. The showcase generator calls this module.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

MODALITIES = ['text', 'table', 'image', 'chart', 'scanned']
JUDGE_FILES = ['independent-judge-text.json', 'independent-judge-table.json', 'independent-judge-visual.json']
SCORES = ['answer_correctness', 'faithfulness', 'answer_relevancy']
CATEGORIES = ['supported', 'partial', 'unsupported', 'none']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric(rows, field):
    values = [r[field] for r in rows if r[field] is not None]
    counts = Counter(str(float(v)).rstrip('0').rstrip('.') if v else '0' for v in values)
    return {'sum': sum(values), 'n': len(values), 'null_n': len(rows) - len(values),
            'mean': sum(values) / len(values) if values else None,
            'score_counts': {key: counts.get(key, 0) for key in ['1', '0.5', '0']}}


def boolean(rows, field):
    values = [r[field] for r in rows if r[field] is not None]
    return {'true_n': sum(v is True for v in values), 'false_n': sum(v is False for v in values),
            'n': len(values), 'null_n': len(rows) - len(values),
            'rate': sum(v is True for v in values) / len(values) if values else None}


def aggregate(rows):
    positive = [r for r in rows if not r['unanswerable']]
    negative = [r for r in rows if r['unanswerable']]
    substantive = [r for r in rows if r['faithfulness'] is not None]
    support = Counter(r['citation_claim_support'] for r in rows)
    judged_support = sum(support[k] for k in CATEGORIES if k != 'none')
    false_refusals = [r['id'] for r in positive if r['saved_abstained']]
    negative_ok = [r['id'] for r in negative if r['saved_abstained'] and r['abstention_appropriate'] is True]
    return {
        'reviewed_n': len(rows), 'answerable_n': len(positive), 'authored_negative_n': len(negative),
        'answerable_correctness': numeric(positive, 'answer_correctness'),
        'authored_negative_correctness': numeric(negative, 'answer_correctness'),
        'all_question_correctness_including_negatives': numeric(rows, 'answer_correctness'),
        'faithfulness': numeric(rows, 'faithfulness'),
        'answer_relevancy': numeric(rows, 'answer_relevancy'),
        'hallucination_all_reviewed': boolean(rows, 'hallucination'),
        'hallucination_answerable': boolean(positive, 'hallucination'),
        'hallucination_substantive_answers': boolean(substantive, 'hallucination'),
        'appropriate_negative_abstention': {'count': len(negative_ok), 'n': len(negative),
            'rate': len(negative_ok) / len(negative) if negative else None, 'ids': negative_ok},
        'false_refusal_on_answerable': {'count': len(false_refusals), 'n': len(positive),
            'rate': len(false_refusals) / len(positive) if positive else None, 'ids': false_refusals},
        'citation_claim_support_per_response': {
            'counts': {k: support.get(k, 0) for k in CATEGORIES}, 'all_reviewed_n': len(rows),
            'substantive_judgment_n': judged_support, 'none_n': support['none'],
            'fully_supported_n': support['supported'],
            'fully_supported_rate_excluding_none': support['supported'] / judged_support if judged_support else None,
            'definition': 'Categorical per-response judgment, not a counted-claim precision/recall metric; partial is not assigned a numeric weight.'},
    }


def collect(evaluation_dir: Path):
    e = evaluation_dir.resolve()
    generation_path = e / 'results/generation-agent.json'
    generation = json.loads(generation_path.read_text())
    final = [r for r in generation['runs'] if r['phase'] == 'final' and r['run'] == 1]
    assert len(final) == 1
    run = final[0]
    original_rows = {r['id']: r for r in run['per_question']}
    assert len(original_rows) == len(run['per_question']) == 43
    assert run['config']['requested_n'] == 60 and run['config']['partial'] is True
    assert generation['partial_final_evidence']['status'] == 'BUDGET_STOPPED_PARTIAL_FINAL'
    sources, normalized = [], {}
    for filename in JUDGE_FILES:
        file = e / 'results' / filename
        review = json.loads(file.read_text())
        judgments = review.get('per_question', review.get('cases'))
        assert judgments and len({r['id'] for r in judgments}) == len(judgments)
        if filename == JUDGE_FILES[0]:
            ref = review['source']
            assert ref['sha256'] == sha(generation_path), 'Text judge source digest changed'
            assert ref['run_id'] == run['run_id']
            dataset, app = ref['dataset_fingerprint'], ref['app_source_fingerprint']
        elif filename == JUDGE_FILES[1]:
            ref = review['scope']
            assert ref['phase'] == 'final' and ref['run'] == 1
            dataset, app = ref['source_dataset_fingerprint'], ref['source_app_fingerprint']
        else:
            assert 'final-run-01' in review['scope']
            dataset, app = review['dataset_fingerprint'], review['app_source_fingerprint']
        assert dataset == run['dataset_fingerprint'] and app == run['app_source_fingerprint']
        sources.append({'file': 'results/' + filename, 'sha256': sha(file), 'reviewed_ids': [r['id'] for r in judgments],
                        'reviewed_n': len(judgments), 'judge_model_id': None})
        for row in judgments:
            identifier = row['id']
            assert identifier in original_rows and identifier not in normalized
            saved = original_rows[identifier]
            if 'question' in row:
                assert row['question'] == saved['question']
            if 'unanswerable' in row:
                assert row['unanswerable'] == saved['unanswerable']
            for field in SCORES:
                assert row[field] is None or (type(row[field]) in (float, int) and row[field] in [0, .5, 1])
            for field in ['hallucination', 'abstention_appropriate']:
                assert row[field] is None or type(row[field]) is bool
            assert row['citation_claim_support'] in CATEGORIES
            assert type(saved['metrics']['abstained']) is bool
            normalized[identifier] = {
                **row, 'modality': saved['modality'], 'unanswerable': saved['unanswerable'],
                'saved_abstained': saved['metrics']['abstained'], 'saved_mode': saved['result'].get('mode'),
                'judgment_source_file': 'results/' + filename,
            }
    assert set(normalized) == set(original_rows), 'Every saved answer must have exactly one judgment'
    rows = [normalized[r['id']] for r in run['per_question']]
    coverage = Counter(r['modality'] for r in rows)
    assert dict(coverage) == {'text': 12, 'table': 12, 'image': 12, 'chart': 7}
    overall = aggregate(rows)
    assert overall['answerable_n'] == 37 and overall['authored_negative_n'] == 6
    return {
        'schema_version': 'independent-codex-review-aggregate-v1',
        'status': 'BOUNDED_REVIEW_OF_STOPPED_GENERATION_PREFIX',
        'method': 'Mechanical aggregation of three existing independent Codex review artifacts; this aggregator does not rejudge or rescore any answer.',
        'reviewer_provenance': {
            'reviewer': 'Three Codex review assignments, one reviewer per text, table, or image/chart partition',
            'judge_model_id': None, 'judge_model_id_reason': 'Exact serving model identifier was not exposed in the review artifacts.',
            'separate_from_answer_generator': True, 'answer_generator': 'Self-hosted qwen3-vl:4b-instruct',
            'external_judge_api_used': False, 'ragas_score': False, 'human_review': False,
            'inter_rater_calibration': False, 'new_application_model_calls': 0,
        },
        'generation_source': {
            'file': 'results/generation-agent.json', 'sha256': sha(generation_path), 'phase': 'final', 'run': 1, 'run_id': run['run_id'],
            'dataset_fingerprint': run['dataset_fingerprint'], 'app_source_fingerprint': run['app_source_fingerprint'],
            'saved_rows_sha256': hashlib.sha256(json.dumps(run['per_question'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        },
        'sources': sources,
        'coverage': {
            'reviewed_n': len(rows), 'saved_generation_n': len(rows), 'planned_generation_n': run['config']['requested_n'],
            'remaining_unreviewed_and_ungenerated_n': run['config']['requested_n'] - len(rows),
            'answerable_n': overall['answerable_n'], 'authored_negative_n': overall['authored_negative_n'],
            'by_modality': {m: coverage.get(m, 0) for m in MODALITIES},
            'sampling': 'Deterministic 43/60 stopped prefix; not randomly sampled. One incomplete run; no scanned generation, second final run, or third-pass consistency sample.',
            'per_modality_mean_weights': 'Overall means weight applicable question rows equally; they do not average modality means.',
        },
        'definitions': {
            'answer_correctness': 'Existing 0/0.5/1 rubric. Answerable-only weighted mean is primary; correct negative abstentions are reported separately. A score of 0.5 is partial credit, not a fully correct answer.',
            'nulls': 'Null score values are excluded from means and explicitly counted. Faithfulness excludes 7 no-substantive-answer refusals; relevancy excludes 6 appropriate authored-negative abstentions.',
            'false_refusal': 'Saved generation metrics.abstained is true AND authored unanswerable is false. Judge abstention_appropriate=false is not itself a refusal; table reviewers also used it for correctly answered positives.',
            'hallucination': 'Existing reviewer explicit unsupported factual-claim flag. Report all-row, answerable, and substantive-answer denominators; a false refusal is not a fabricated fact.',
            'citation_support': 'Existing supported/partial/unsupported/none category per answer; no fabricated claim counts or numeric partial weights. Claim-count citation precision and recall remain NOT MEASURED.',
        },
        'overall': overall,
        'by_modality': {m: aggregate([r for r in rows if r['modality'] == m]) for m in MODALITIES},
        'visual_answerable': aggregate([r for r in rows if r['modality'] in ['image', 'chart'] and not r['unanswerable']]),
        'failure_ids': {
            'not_fully_correct_answerable': [r['id'] for r in rows if not r['unanswerable'] and r['answer_correctness'] < 1],
            'hallucination': [r['id'] for r in rows if r['hallucination'] is True],
            'false_refusal': overall['false_refusal_on_answerable']['ids'],
            'partial_citation_support': [r['id'] for r in rows if r['citation_claim_support'] == 'partial'],
        },
        'not_measured': [
            'Exact semantic context precision@5 and context recall: contexts were not independently scored as complete ranked sets.',
            'Claim-count citation precision/recall: judgments are categorical per answer, without claim enumeration.',
            'External RAGAS LLM-judge scores: no external judge call or credential; these separately named Codex review scores do not fill frozen RAGAS fields.',
            'Scanned-PDF generation quality: zero saved generation responses; scanned ingestion metrics remain a separate scope.',
            'Population/production accuracy, repeat-run stability, inter-rater agreement, and statistical confidence for this review.',
        ],
        'limitations': [
            'Fictional authored PDFs and non-random incomplete coverage; 43/60 is not a full multimodal benchmark.',
            'Text review used saved excerpts/references; table and visual reviews also inspected source PDF pages. Original pages may contain evidence absent from the exact OCR quote.',
            'Different reviewer partitions are not multiple ratings of the same answers; no inter-rater calibration or human expert adjudication.',
            'Faithfulness can be high for a relevant-source quotation that still fails to answer the question; visual failure IDs must be read alongside correctness and relevancy.',
            'No matched-subset independent baseline review exists, so this review does not establish semantic improvement over baseline.',
        ],
        'per_question': rows,
    }


def fmt_score(metric):
    if not metric['n']:
        return f'NOT MEASURED (n=0; null={metric["null_n"]})'
    return f'{metric["sum"]:g}/{metric["n"]} = {metric["mean"]:.6f} (null={metric["null_n"]})'


def fmt_rate(count, n):
    return 'NOT MEASURED (n=0)' if not n else f'{count}/{n} = {count/n:.6f}'


def support_label(metric):
    counts = metric['counts']
    return f'{counts["supported"]} supported / {counts["partial"]} partial / {counts["unsupported"]} unsupported / {counts["none"]} none'


def markdown(summary, standalone=False):
    data = summary['overall']
    lines = ['# Independent Codex review of saved HomeAtlas answers' if standalone else '## Independent Codex review of saved answers', '',
        '**Bounded review: 43/60 questions from one stopped generation run; 37 answerable, 6 authored negatives, and no scanned-PDF generation.** Three independent Codex review assignments covered disjoint text, table, and visual partitions. This is not a RAGAS score, human review, calibrated multi-rater evaluation, or production accuracy estimate. The exact Codex serving model ID was unavailable; the answer generator was the separate self-hosted `qwen3-vl:4b-instruct`.', '',
        f'Primary answerable correctness: **{fmt_score(data["answerable_correctness"])}**. This includes 30 fully correct answers, one half-credit answer, and six zero-credit answers. The six authored negatives are separate: **{fmt_rate(data["appropriate_negative_abstention"]["count"], data["appropriate_negative_abstention"]["n"])} appropriate abstentions**. Including those negatives would give {fmt_score(data["all_question_correctness_including_negatives"])}; that is not the answerable-only correctness score.', '',
        '| Review measure | Exact accounting |', '| --- | --- |',
        f'| Faithfulness | {fmt_score(data["faithfulness"])}; seven non-substantive refusals excluded |',
        f'| Answer relevancy | {fmt_score(data["answer_relevancy"])}; six appropriate negative abstentions excluded |',
        f'| Explicit hallucination flags, all reviewed answers | {fmt_rate(data["hallucination_all_reviewed"]["true_n"], data["hallucination_all_reviewed"]["n"])} |',
        f'| Explicit hallucination flags, answerable only | {fmt_rate(data["hallucination_answerable"]["true_n"], data["hallucination_answerable"]["n"])} |',
        f'| Explicit hallucination flags, substantive answers only | {fmt_rate(data["hallucination_substantive_answers"]["true_n"], data["hallucination_substantive_answers"]["n"])} |',
        f'| False refusals on answerable questions | {fmt_rate(data["false_refusal_on_answerable"]["count"], data["false_refusal_on_answerable"]["n"])} (`text-10`) |',
        f'| Citation claim support, categorical per answer | {support_label(data["citation_claim_support_per_response"])} |',
        f'| Fully supported citation judgments, excluding none | {fmt_rate(data["citation_claim_support_per_response"]["fully_supported_n"], data["citation_claim_support_per_response"]["substantive_judgment_n"])}; not claim-count precision/recall |', '',
        'Null faithfulness/relevancy values are excluded, not converted into zero or one. Hallucination rates count explicit unsupported factual-claim flags, not refusals. A table reviewer used `abstention_appropriate=false` for correctly answered positives, so false refusals are derived from saved `metrics.abstained` and authored answerability.', '',
        '| Modality | Reviewed / answerable / negatives | Answerable correctness | Negative abstention | Faithfulness | Relevancy | Hallucination flags (all reviewed) | Citation support: supported / partial / unsupported / none |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for modality, d in summary['by_modality'].items():
        a = d['appropriate_negative_abstention']; h = d['hallucination_all_reviewed']; counts = d['citation_claim_support_per_response']['counts']
        lines.append(f'| {modality} | {d["reviewed_n"]} / {d["answerable_n"]} / {d["authored_negative_n"]} | {fmt_score(d["answerable_correctness"])} | {fmt_rate(a["count"], a["n"])} | {fmt_score(d["faithfulness"])} | {fmt_score(d["answer_relevancy"])} | {fmt_rate(h["true_n"], h["n"])} | '+ ' / '.join(str(counts[k]) for k in CATEGORIES)+' |')
    lines += ['', '**Observed failures must remain visible.** `text-10` falsely refused the answerable four-unit service-interval summary. `image-02`, `image-04`, and `image-10` quoted labels but omitted the requested visual relationships. `chart-01` did not bind March to its usage and `chart-02` did not state the trend. `image-06` received half credit and an unsupported-claim flag; `image-08` answered the core question correctly but also received an unsupported-claim flag. Partial citation support also includes unrelated citations in `chart-03` and `chart-07`. These are the original reviewers’ findings, not new judgments by the aggregator.', '',
        f'For the 17 answerable image/chart cases combined, correctness is {fmt_score(summary["visual_answerable"]["answerable_correctness"])}. High faithfulness of quoted material does not establish that the response answered its visual question.', '',
        'Still **NOT MEASURED**: exact semantic context precision@5/recall, claim-count citation precision/recall, external RAGAS LLM-judge scores, scanned generation quality, inter-rater agreement, repeat-run semantic stability, and production generalization. No confidence interval or baseline semantic-improvement claim is added for this review.', '',
        'Artifacts: [aggregate JSON](results/independent-judge-summary.json), [text judgments](results/independent-judge-text.json), [table judgments](results/independent-judge-table.json), [visual judgments](results/independent-judge-visual.json). '+('The showcase report incorporates this same aggregation.' if standalone else 'Full review and provenance: [independent review](INDEPENDENT_JUDGE_REVIEW.md).')]
    if standalone:
        source = summary['generation_source']
        lines += ['', '## Provenance and regeneration', '',
            f'Saved generation source: `{source["file"]}`, `{source["run_id"]}`, SHA-256 `{source["sha256"]}`.',
            f'Dataset fingerprint: `{source["dataset_fingerprint"]}`. Application source fingerprint: `{source["app_source_fingerprint"]}`.', '',
            '| Review input | SHA-256 | Questions |', '| --- | --- | --- |']
        lines += [f'| `{s["file"]}` | `{s["sha256"]}` | {s["reviewed_n"]} |' for s in summary['sources']]
        lines += ['', 'The aggregator checks source fingerprints/digests, unique IDs, exact 43-row coverage, rubric score types, and answerability against saved generation data. It recomputes every numerator and denominator from case rows; source-artifact summaries are not trusted as aggregates. No new app inference or judge scoring runs.', '',
            '```sh', 'python3 evaluation/showcase/independent_review.py', 'evaluation/.venv/bin/python evaluation/showcase/report.py --app-root "$PWD"', '```', '',
            'The first command regenerates the aggregate JSON and this review; the second regenerates the showcase JSON and report with the same review section and coverage rows. The frozen original evaluation runner remains historical and unchanged; do not invoke it to replace this budget-limited showcase report.', '',
            'Evidence limits: text review used saved excerpts/references; table and visual reviewers inspected original fictional pages. Some original pages contain facts absent from the exact OCR excerpt. No multiple-rater agreement or human expert adjudication was performed. The non-random stopped prefix and one observed generation run cannot estimate real-household or scanned-document performance.', '']
    return lines


def write(evaluation_dir, summary):
    (evaluation_dir / 'results').mkdir(parents=True, exist_ok=True)
    (evaluation_dir / 'results/independent-judge-summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    (evaluation_dir / 'INDEPENDENT_JUDGE_REVIEW.md').write_text('\n'.join(markdown(summary, standalone=True)))


def bind(data, summary):
    assert data['app_source_fingerprint'] == summary['generation_source']['app_source_fingerprint']
    assert data['dataset_fingerprint'] == summary['generation_source']['dataset_fingerprint']
    data['independent_review'] = summary
    data['not_measured'] = [s for s in data['not_measured'] if not s.startswith(('Independent-judge faithfulness/', 'External RAGAS LLM-judge scores:'))]
    note = 'External RAGAS LLM-judge metrics and exact semantic context precision/recall: NOT MEASURED. Separate bounded Codex review covers 43 saved answers.'
    if note not in data['not_measured']:
        data['not_measured'].insert(0, note)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-dir', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    summary = collect(args.evaluation_dir)
    write(args.evaluation_dir, summary)
    print(json.dumps({'reviewed_n': summary['coverage']['reviewed_n'], 'answerable_correctness': summary['overall']['answerable_correctness'], 'output': 'results/independent-judge-summary.json'}))


if __name__ == '__main__':
    main()
