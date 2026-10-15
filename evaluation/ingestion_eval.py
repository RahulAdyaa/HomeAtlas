"""Measure the unchanged production parser against frozen, authored PDF gold.

No model answers, OCR outputs, inferred table structures or figure captions become
reference data. OCR CER/WER are measured only where an authored reading order exists
(scanned pages); diagnostics on chart labels never claim chart understanding.
"""
from __future__ import annotations

import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
import unicodedata
from unittest.mock import patch

EVALUATION = Path(__file__).resolve().parent
APP_ROOT = Path(os.environ.get('EVAL_APP_ROOT', EVALUATION.parent)).resolve()
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(EVALUATION))

from protocol import (SEED, argument_parser, canonical_chunks, frozen_dataset,
                      make_result, metric, questions, write_result)


def normalized(value: str) -> str:
    """CER/WER: NFKC, casefold, whitespace collapse; punctuation is retained."""
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def tokens(value: str) -> list[str]:
    """Literal evidence matching; boundaries avoid number 3 matching 30."""
    return re.findall(r'\w+', unicodedata.normalize('NFKC', value).casefold())


def contains(text: str, phrase: str) -> bool:
    haystack, needle = tokens(text), tokens(phrase)
    return bool(needle) and any(haystack[i:i + len(needle)] == needle
                              for i in range(len(haystack) - len(needle) + 1))


def edit_distance(reference, hypothesis) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, item in enumerate(reference, 1):
        current = [i]
        for j, other in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (item != other)))
        previous = current
    return previous[-1]


def error_counts(reference: str, hypothesis: str) -> dict:
    ref, hyp = normalized(reference), normalized(hypothesis)
    ref_words, hyp_words = ref.split(), hyp.split()
    return {'character_edits': edit_distance(ref, hyp), 'reference_characters': len(ref),
            'word_edits': edit_distance(ref_words, hyp_words), 'reference_words': len(ref_words)}


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError('Cannot calculate a quantile without observations')
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def leaf_text(chunks: list[dict]) -> str:
    """Avoid counting OCR context copies as additional recognized words."""
    return '\n'.join(c['metadata']['content_text'] for c in chunks
                     if not c.get('metadata', {}).get('ocr_context'))


def page_chunks(corpus: list[dict], source: str, page: int) -> list[dict]:
    return [c for c in corpus if c['fixture_source_id'] == source and c['page'] == page]


def safe_chunk(chunk: dict, artifact_root: Path) -> dict:
    row = dict(chunk)
    if row.get('image_path'):
        path = Path(row['image_path'])
        row['image_path'] = 'evaluation/runtime/' + str(path.relative_to(artifact_root.parent))
    return row


def measured_mean(name: str, values: list[float], **extra) -> dict:
    return metric(name, statistics.mean(values) if values else None, len(values),
                  reason=None if values else 'No eligible observations.', **extra)


def extract_corpus(phase: str, run: int) -> tuple[list[dict], list[dict], dict]:
    import fitz
    import pytesseract
    from worker import ingestion
    from worker.config import settings

    manifest = json.loads((EVALUATION / 'fixtures/manifest.json').read_text())
    annotations = questions('pdf')
    locations = {q['modality']: q['location_path'] for q in annotations}
    runtime = Path(os.environ.get('EVAL_SHARED_RUNTIME', EVALUATION / 'runtime'))
    artifact_root = runtime / f'ingestion-{phase}-run-{run}'
    artifact_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    all_chunks, page_rows, documents = [], [], []
    ocr_calls = []
    original_ocr = pytesseract.image_to_data
    original_get_text = fitz.Page.get_text
    active = {'document': None, 'page': None, 'started': None}

    def finish_page(ended: float):
        if active['started'] is not None:
            page_rows.append({'id': f"ingestion-page-{active['document']}-{active['page']}",
                              'kind': 'page', 'fixture_source_id': active['document'],
                              'page': active['page'],
                              'parser_seconds': ended - active['started']})
            active['started'] = None

    def timed_get_text(page, *args, **kwargs):
        started = time.perf_counter()
        finish_page(started)
        active.update(page=page.number + 1, started=started)
        return original_get_text(page, *args, **kwargs)

    def observed_ocr(*args, **kwargs):
        started = time.perf_counter()
        entry = {'fixture_source_id': active['document'], 'page': active['page'],
                 'language': kwargs.get('lang'), 'config': kwargs.get('config')}
        try:
            value = original_ocr(*args, **kwargs)
            entry['status'] = 'success'
            return value
        except Exception as error:
            entry.update(status='failure', exception_type=type(error).__name__)
            raise
        finally:
            entry['seconds'] = time.perf_counter() - started
            ocr_calls.append(entry)

    with patch.object(fitz.Page, 'get_text', timed_get_text), \
            patch.object(pytesseract, 'image_to_data', observed_ocr):
        for document in manifest:
            source = document['id']
            active.update(document=source, page=None, started=None)
            started = time.perf_counter()
            status, error_type = 'success', None
            try:
                extracted = ingestion.extract(EVALUATION / document['file'], 'application/pdf',
                                               artifact_root / source, settings)
                canonical = canonical_chunks(extracted, source, f'{source}.pdf', locations[source])
            except Exception as error:
                status, error_type, canonical = 'failure', type(error).__name__, []
            ended = time.perf_counter()
            finish_page(ended)
            all_chunks.extend(canonical)
            documents.append({'fixture_source_id': source, 'pages': len(document['pages']),
                              'parser_seconds': ended - started, 'status': status,
                              'exception_type': error_type, 'chunk_count': len(canonical)})
            print(json.dumps({'document': source, 'phase': phase, 'run': run,
                              'status': status, 'chunks': len(canonical)}), flush=True)

    for row in page_rows:
        selected = page_chunks(all_chunks, row['fixture_source_id'], row['page'])
        row.update(chunk_count=len(selected), leaf_text=leaf_text(selected),
                   chunks=[safe_chunk(c, artifact_root) for c in selected],
                   ocr_calls=[c for c in ocr_calls if c['fixture_source_id'] == row['fixture_source_id']
                              and c['page'] == row['page']])
    observed = {'ocr_backend': settings.ocr_backend, 'ocr_languages_configured': settings.ocr_languages,
                'ocr_languages_available': sorted(pytesseract.get_languages(config='')),
                'tesseract_version': str(pytesseract.get_tesseract_version()),
                'packages': {name: importlib.metadata.version(name)
                             for name in ['PyMuPDF', 'Pillow', 'pytesseract']},
                'documents': documents, 'ocr_invocations': ocr_calls,
                'actual_llm_calls': 0, 'parser_cache_replay': False,
                'safe_settings': {'max_pdf_pages': settings.max_pdf_pages, 'max_bytes': settings.max_bytes},
                'timing_scope': 'Actual parser, page render, OCR and chunk assembly. Excludes embeddings, database writes and queue wait. Page starts are instrumented at Page.get_text; file validation/open time remains document overhead. Shared-machine load is uncontrolled.'}
    return all_chunks, page_rows, observed


def score(corpus: list[dict], page_rows: list[dict], observed: dict) -> tuple[list[dict], list[dict]]:
    manifest = json.loads((EVALUATION / 'fixtures/manifest.json').read_text())
    metrics, rows = [], list(page_rows)
    page_map = {(p['fixture_source_id'], p['page']): p for p in page_rows}
    error_pages = []
    native_error_pages = []
    table_cells, table_pages, figures, chart_values, chart_labels, image_labels = [], [], [], [], [], []

    for document in manifest:
        source = document['id']
        if source in {'scanned', 'text'}:
            destination = error_pages if source == 'scanned' else native_error_pages
            for gold in document['pages']:
                page = page_map.get((source, gold['page']))
                counts = error_counts(gold['text'], page['leaf_text'] if page else '')
                row = {'id': f'ocr-{source}-{gold["page"]}', 'kind': 'ocr-reference',
                       'fixture_source_id': source, 'page': gold['page'],
                       'reference': gold['text'], **counts,
                       'cer': counts['character_edits'] / counts['reference_characters'],
                       'wer': counts['word_edits'] / counts['reference_words']}
                rows.append(row)
                destination.append(row)
        for table in document['tables']:
            selected = page_chunks(corpus, source, table['page'])
            text = leaf_text(selected)
            cells_present = []
            for r, cells in enumerate(table['cells']):
                for c, value in enumerate(cells):
                    present = contains(text, value)
                    cell = {'id': f'table-cell-{table["page"]}-{r}-{c}', 'kind': 'table-cell-text',
                            'fixture_source_id': source, 'page': table['page'],
                            'row': r, 'column': c, 'reference_cell': value,
                            'literal_text_present': present}
                    table_cells.append(cell)
                    cells_present.append(present)
                    rows.append(cell)
            table_sequence = ' '.join(value for cells in table['cells'] for value in cells)
            single_chunk = any(contains(c['metadata']['content_text'], table_sequence) for c in selected)
            row = {'id': f'table-{table["page"]}', 'kind': 'table', 'page': table['page'],
                   'fixture_source_id': source, 'all_cell_text_present': all(cells_present),
                   'row_major_token_sequence_preserved': contains(text, table_sequence),
                   'entire_table_in_single_chunk': single_chunk,
                   'structured_table_output': any(
                       any(key in c['metadata'] for key in ['cells', 'rows', 'columns', 'table'])
                       or c.get('modality') == 'table' for c in selected)}
            table_pages.append(row)
            rows.append(row)
        for figure in document['figures']:
            selected = page_chunks(corpus, source, figure['page'])
            text = leaf_text(selected)
            paths = {c.get('image_path') for c in selected if c.get('image_path')}
            row = {'id': f'figure-{source}-{figure["page"]}', 'kind': 'figure-asset',
                   'fixture_source_id': source, 'page': figure['page'], 'gold_bbox': figure['bbox'],
                   'page_preview_retained': any(Path(path).is_file() for path in paths),
                   'figure_region_detector_output': False,
                   'facts': [{'literal': fact, 'present': contains(text, fact)} for fact in figure['facts']]}
            if source == 'image':
                row['all_label_and_caption_facts_in_single_chunk'] = any(
                    all(contains(c['metadata']['content_text'], fact) for fact in figure['facts'])
                    and bool(c.get('image_path')) for c in selected)
                for fact in row['facts']:
                    image_labels.append({'id': f'image-label-{figure["page"]}-{fact["literal"]}',
                                         'kind': 'image-literal', 'page': figure['page'], **fact})
            else:
                for fact in row['facts'][:3]:
                    chart_values.append({'id': f'chart-value-{figure["page"]}-{fact["literal"]}',
                                         'kind': 'chart-value-literal', 'page': figure['page'], **fact})
                for fact in row['facts'][3:]:
                    chart_labels.append({'id': f'chart-label-{figure["page"]}-{fact["literal"]}',
                                         'kind': 'chart-label-literal', 'page': figure['page'], **fact})
            figures.append(row)
            rows.append(row)

    for prefix, eligible in [('ocr.scanned', error_pages), ('native_text', native_error_pages)]:
        metrics.extend([
            metric(f'{prefix}.cer_micro', sum(r['character_edits'] for r in eligible) /
                   sum(r['reference_characters'] for r in eligible), len(eligible),
                   reference_characters=sum(r['reference_characters'] for r in eligible)),
            metric(f'{prefix}.wer_micro', sum(r['word_edits'] for r in eligible) /
                   sum(r['reference_words'] for r in eligible), len(eligible),
                   reference_words=sum(r['reference_words'] for r in eligible)),
            measured_mean(f'{prefix}.cer_macro', [r['cer'] for r in eligible]),
            measured_mean(f'{prefix}.wer_macro', [r['wer'] for r in eligible])])
    metrics.extend([
        measured_mean('table.cell_text_recall', [int(c['literal_text_present']) for c in table_cells],
                      interpretation='Whole-token cell text present on correct source page. Does not establish row/column association.'),
        measured_mean('table.row_major_text_sequence_preserved_rate',
                      [int(r['row_major_token_sequence_preserved']) for r in table_pages],
                      interpretation='Flattened row-major token sequence, not a structured table or TEDS score.'),
        measured_mean('table.structured_output_rate', [int(r['structured_table_output']) for r in table_pages]),
        metric('table.cell_accuracy', None, 0,
               reason='Production PDF parser emits flat text chunks, not aligned table cells; cell accuracy would require inventing row/column reconstruction.'),
        metric('table.structure_teds', None, 0,
               reason='No structured HTML/table tree is emitted by the production PDF parser.'),
        metric('figure.detection_recall', None, 0,
               reason='Production parser has raster-region OCR and page previews but no figure-region detector output. Preview retention is measured separately.'),
        measured_mean('figure.page_preview_retention_rate', [int(r['page_preview_retained']) for r in figures]),
        measured_mean('image.literal_label_recall', [int(r['present']) for r in image_labels],
                      interpretation='Frozen literal labels/identifiers/numbers only; does not measure colors, arrows, spatial relations or semantic understanding.'),
        measured_mean('chart.numeric_label_text_recall', [int(r['present']) for r in chart_values],
                      interpretation='A printed value token exists on the correct chart page. Does not establish association with a bar or month.'),
        measured_mean('chart.axis_legend_text_recall', [int(r['present']) for r in chart_labels]),
        metric('chart.structured_reading_accuracy', None, 0,
               reason='Ingestion does not emit bar-to-value/month associations. End-to-end chart QA is evaluated by the generation specialist.'),
        metric('image.caption_quality', None, 0,
               reason='Ingestion does not generate semantic captions; no free-tier external judge credentials are configured.'),
        metric('image.hallucinated_content_rate', None, 0,
               reason='Ingestion emits OCR text and visual anchors, not generated descriptions. Semantic unsupported-content judging requires an unavailable external judge; OCR substitution errors are measured as CER/WER.'),
        measured_mean('chunking.table_split_rate', [int(not r['entire_table_in_single_chunk']) for r in table_pages]),
        measured_mean('chunking.figure_label_caption_single_chunk_rate',
                      [int(r['all_label_and_caption_facts_in_single_chunk']) for r in figures if r['fixture_source_id'] == 'image'],
                      interpretation='Printed diagram labels and caption facts co-occur in one chunk with a source image; no semantic caption score.')])

    evidence_rows = []
    for q in questions('pdf'):
        if q['unanswerable']:
            continue
        selected = [c for c in corpus if c['fixture_source_id'] == q['modality'] and c['page'] in q['source_pages']]
        gold_terms = q['evidence_terms']
        joined = '\n'.join(c['metadata']['content_text'] for c in selected)
        covered = [contains(joined, term) for term in gold_terms]
        single_chunk = any(all(contains(c['metadata']['content_text'], term) for term in gold_terms) for c in selected)
        row = {'id': q['id'], 'kind': 'question-evidence', 'modality': q['modality'],
               'type': q['type'], 'source_pages': q['source_pages'],
               'evidence_terms': gold_terms, 'literal_term_covered': covered,
               'all_terms_present': all(covered), 'all_terms_in_single_chunk': single_chunk,
               'term_coverage': sum(covered) / len(covered),
               'reference_spans_multiple_pages': len(q['source_pages']) > 1,
               'eligible_chunk_ids': [c['id'] for c in selected]}
        evidence_rows.append(row)
        rows.append(row)
    for modality in ['overall', 'text', 'table', 'image', 'chart', 'scanned']:
        selected = [r for r in evidence_rows if modality == 'overall' or r['modality'] == modality]
        metrics.extend([
            measured_mean(f'chunking.{modality}.literal_evidence_term_coverage', [r['term_coverage'] for r in selected]),
            measured_mean(f'chunking.{modality}.literal_evidence_all_terms_rate', [int(r['all_terms_present']) for r in selected]),
            measured_mean(f'chunking.{modality}.literal_evidence_single_chunk_rate', [int(r['all_terms_in_single_chunk']) for r in selected]),
            measured_mean(f'chunking.{modality}.reference_evidence_spread_rate',
                          [int(r['all_terms_present'] and not r['all_terms_in_single_chunk']) for r in selected],
                          interpretation='Literal terms present across chunks but absent together in a single chunk; deliberate multi-page questions can require this.')])
    metrics.append(metric('chunking.semantic_answer_completeness', None, 0,
                          reason='Literal evidence diagnostics are not semantic completeness; no external judge key is configured.'))
    for modality in ['overall', 'text', 'table', 'image', 'chart', 'scanned']:
        selected = [c for c in corpus if modality == 'overall' or c['fixture_source_id'] == modality]
        lengths = [len(c['metadata']['content_text']) for c in selected]
        prefixed = [len(c['text']) for c in selected]
        words = [len(c['metadata']['content_text'].split()) for c in selected]
        for suffix, values in [('content_characters', lengths), ('indexed_characters', prefixed), ('whitespace_words', words)]:
            for statistic, function in [('mean', statistics.mean), ('min', min), ('max', max),
                                        ('p50', lambda x: quantile(x, .5)), ('p95', lambda x: quantile(x, .95))]:
                metrics.append(metric(f'chunking.{modality}.{suffix}_{statistic}', function(values) if values else None,
                                      len(values), reason=None if values else 'No chunks extracted.'))
        metrics.append(measured_mean(f'chunking.{modality}.location_prefix_and_metadata_rate',
                       [int(c['text'].startswith(f"Location: {c['location_path']}\n\n") and
                            c['metadata']['location_path'] == c['location_path']) for c in selected]))
        pages = [r for r in page_rows if modality == 'overall' or r['fixture_source_id'] == modality]
        metrics.extend([measured_mean(f'ingestion.{modality}.parser_seconds_per_page_mean', [r['parser_seconds'] for r in pages]),
                        metric(f'ingestion.{modality}.parser_seconds_per_page_p50', quantile([r['parser_seconds'] for r in pages], .5) if pages else None,
                               len(pages), reason=None if pages else 'No pages were processed.'),
                        metric(f'ingestion.{modality}.parser_seconds_per_page_p95', quantile([r['parser_seconds'] for r in pages], .95) if pages else None,
                               len(pages), reason=None if pages else 'No pages were processed.')])
    metrics.extend([
        measured_mean('ingestion.document_success_rate', [int(d['status'] == 'success') for d in observed['documents']]),
        metric('ingestion.actual_ocr_invocations', len(observed['ocr_invocations']), len(observed['ocr_invocations'])),
        metric('ingestion.actual_llm_calls', observed['actual_llm_calls'], len(observed['documents'])),
        metric('ingestion.embedding_and_database_seconds_per_page', None, 0,
               reason='This specialist measures the actual parser directly; queue, embedding and database stage timings are outside this instrumentation.')])
    rows.extend(image_labels + chart_values + chart_labels)
    return metrics, rows


def main():
    parser = argument_parser(__doc__)
    args = parser.parse_args()
    frozen_dataset()
    random.seed(SEED)
    corpus, pages, observed = extract_corpus(args.phase, args.run)
    metrics, rows = score(corpus, pages, observed)
    config = {'group': 'F', 'measurement_version': 1,
              'suite': {'documents': 5, 'pages': 20, 'pdf_questions': 60, 'answerable_questions': 50},
              'normalization': 'NFKC, casefold and whitespace collapse for OCR; punctuation retained. Evidence matching uses contiguous whole-word tokens.',
              'ocr_reference': 'Frozen manifest scanned-page text, authored by build_testset.py; native text measured separately. No chart OCR CER/WER because no single authored chart reading order exists.',
              'table_policy': 'Cell string presence and row-major flattened sequence are diagnostics. No inferred structured table replaces production parser output.',
              'visual_policy': 'Printed fact tokens and page preview retention are diagnostics, not semantic figure detection/caption/chart understanding.',
              'fresh_extraction': True, 'generation_or_judge_cache_used': False,
              'external_judge': {'model': None, 'status': 'NOT MEASURED', 'reason': 'No free-tier external judge key configured.'},
              'observed_runtime': observed}
    for row in rows:
        row['run_id'] = f'{args.phase}-run-{args.run:02}'
    result = make_result('ingestion-agent', args.phase, args.run, metrics, rows, config, APP_ROOT)
    result['models']['observed'] = {key: observed[key] for key in ['ocr_backend', 'ocr_languages_configured', 'ocr_languages_available', 'tesseract_version', 'packages']}
    write_result(args.output, result)
    print(json.dumps({'saved': str(args.output), 'metrics': len(metrics), 'rows': len(rows),
                      'phase': args.phase, 'run': args.run}), flush=True)


if __name__ == '__main__':
    main()
