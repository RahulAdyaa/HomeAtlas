from dataclasses import replace
import io
from pathlib import Path
from types import SimpleNamespace
import uuid
import zipfile

import fitz
from PIL import Image, ImageDraw, ImageFont
import pytest

from worker.config import Settings
from worker.ingestion import extract, validate_file, split_text
from worker.retrieval import rank_candidates, answer_from_evidence


def write_xlsx(path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr('xl/workbook.xml', '''<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Appliances" sheetId="1" r:id="rId1"/></sheets></workbook>''')
        workbook.writestr('xl/_rels/workbook.xml.rels', '''<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="worksheet"/></Relationships>''')
        workbook.writestr('xl/sharedStrings.xml', '''<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Item</t></si><si><t>Warranty</t></si><si><t>Washer</t></si><si><t>Expires 2028</t></si></sst>''')
        workbook.writestr('xl/worksheets/sheet1.xml', '''<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row><row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row></sheetData></worksheet>''')


class NoModels:
    cfg = SimpleNamespace(image_model='')
    text_identity = 'test-text@1'
    image_identity = 'test-image@1'
    status = {}

    def embed_text(self, *args, **kwargs):
        return None

    def embed_image_space(self, **kwargs):
        return None

    def rerank(self, *args):
        return None

    def generate(self, *args, **kwargs):
        return None


def row(text, **kwargs):
    return dict(id=uuid.uuid4(), source_id=uuid.uuid4(), version_id=uuid.uuid4(), title='Test manual',
                text=text, page=2, bbox=[20, 30, 400, 500], **kwargs)


def test_pdf_keeps_page_and_exact_region(tmp_path):
    path = tmp_path / 'manual.pdf'
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 60), 'AirOne AP-200 manual')
    page.insert_text((40, 100), 'Replacement filter: HA-200. Replace every six months.')
    page = document.new_page()
    page.insert_text((40, 100), 'Warranty expires 12 February 2028.')
    document.save(path)
    chunks = extract(path, 'application/pdf', tmp_path / 'derived')
    assert len(chunks) == 2
    assert chunks[0].page == 1 and 'HA-200' in chunks[0].text
    assert chunks[1].page == 2 and '2028' in chunks[1].text
    assert 30 < chunks[0].bbox[0] < 50
    assert chunks[0].metadata['coordinates'] == 'pdf-points'


def test_image_ocr_is_real(tmp_path):
    path = tmp_path / 'label.png'
    image = Image.new('RGB', (1000, 250), 'white')
    draw = ImageDraw.Draw(image)
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 45) if Path(font_path).exists() else ImageFont.load_default(size=35)
    draw.text((40, 65), 'AirOne filter HA-200', fill='black', font=font)
    image.save(path)
    chunks = extract(path, 'image/png', tmp_path / 'derived')
    assert 'HA-200' in ' '.join(chunk.text for chunk in chunks)
    assert chunks[0].bbox and chunks[0].image_path == str(path)


def test_rejects_signature_mismatch(tmp_path):
    path = tmp_path / 'fake.pdf'
    path.write_text('not a PDF')
    with pytest.raises(ValueError, match='signature'):
        validate_file(path, 'application/pdf')


def test_txt_and_csv_are_searchable_and_keep_row_provenance(tmp_path):
    text = tmp_path / 'notes.txt'
    text.write_text('Filter replacement every six months.\nKeep receipt in kitchen.', encoding='utf-8')
    text_chunks = extract(text, 'text/plain', tmp_path / 'derived-text')
    assert 'six months' in text_chunks[0].text
    assert text_chunks[0].metadata['extractor'] == 'text'

    csv_file = tmp_path / 'records.csv'
    csv_file.write_text('Item,Warranty\nWasher,Expires 2028\n', encoding='utf-8')
    csv_chunks = extract(csv_file, 'text/csv', tmp_path / 'derived-csv')
    assert 'Washer' in csv_chunks[0].text and 'Expires 2028' in csv_chunks[0].text
    assert csv_chunks[0].metadata == {'sheet': 'CSV', 'row_start': 1, 'row_end': 2, 'extractor': 'csv'}


def test_xlsx_extracts_cached_cell_values_with_sheet_and_row_citations(tmp_path):
    path = tmp_path / 'records.xlsx'
    write_xlsx(path)
    chunks = extract(path, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', tmp_path / 'derived-xlsx')
    assert len(chunks) == 1
    assert 'Appliances' in chunks[0].text and 'Washer' in chunks[0].text and 'Expires 2028' in chunks[0].text
    assert chunks[0].metadata == {'sheet': 'Appliances', 'row_start': 1, 'row_end': 2, 'extractor': 'xlsx'}


def test_rejects_invalid_excel_archive(tmp_path):
    path = tmp_path / 'broken.xlsx'
    path.write_bytes(b'not a workbook')
    with pytest.raises(ValueError, match='Invalid Excel'):
        validate_file(path, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


def test_private_path_blocks_escape_and_symlink(tmp_path):
    private = tmp_path / 'private'
    private.mkdir()
    secret = tmp_path / 'secret'
    secret.write_text('secret')
    (private / 'link').symlink_to(secret)
    cfg = replace(Settings(), storage=private)
    with pytest.raises(ValueError, match='outside'):
        cfg.private_path(str(private / 'link'))


def test_hybrid_never_compares_different_embedding_spaces():
    class Vectors(NoModels):
        def embed_text(self, *args, **kwargs):
            return [[1, 0]]
    docs = [row('Kitchen pipe', embedding=[1000, 0], embedding_model='wrong@1'),
            row('The purifier uses filter HA-200.', embedding=[0, 1], embedding_model='test-text@1')]
    result = rank_candidates('Which filter fits?', docs, Vectors())
    assert result[0]['text'] == docs[1]['text']
    assert all(candidate['dense_score'] < 2 for candidate in result)


def test_missing_evidence_abstains():
    candidates = rank_candidates('When does my refrigerator warranty expire?', [row('The carpet is made from wool.')], NoModels())
    result = answer_from_evidence('When does my refrigerator warranty expire?', candidates, NoModels())
    assert result['mode'] == 'abstention' and not result['citations']


def test_missing_models_return_explicit_extractive_mode():
    result = answer_from_evidence('Which filter fits?', [row('Replacement filter HA-200.', lexical_score=1)], NoModels())
    assert result['mode'] == 'extractive'
    assert result['citations'][0]['text'] in result['answer']


def test_fabricated_model_quote_is_rejected():
    class Hallucinating(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Your warranty lasts forever.'}]}
    result = answer_from_evidence('Warranty?', [row('Warranty expires February 2028.')], Hallucinating())
    assert result['mode'] == 'abstention' and not result['citations']


def test_valid_quote_keeps_immutable_provenance():
    document = row('Replacement filter HA-200.', lexical_score=1)
    class Grounded(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Replacement filter HA-200.'}], 'insufficient': False}
    result = answer_from_evidence('Which filter fits?', [document], Grounded())
    citation = result['citations'][0]
    assert result['mode'] == 'local-model-grounded'
    assert citation['sourceId'] == str(document['source_id'])
    assert citation['versionId'] == str(document['version_id'])
    assert citation['page'] == 2 and citation['bbox'] == document['bbox']


def test_conflicting_evidence_is_explicit():
    class Conflicted(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Warranty expires 2028.'}, {'index': 1, 'quote': 'Warranty expires 2029.'}], 'conflict': True}
    result = answer_from_evidence('Warranty?', [row('Warranty expires 2028.'), row('Warranty expires 2029.')], Conflicted())
    assert result['confidence'] == 'conflicting' and len(result['citations']) == 2


def test_model_whitespace_returns_exact_original_span():
    document = row('Hold the filter button\nfor 5 seconds to reset.', lexical_score=1)
    class Flattened(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Hold the filter button for 5 seconds to reset.'}]}
    reply = answer_from_evidence('How to reset?', [document], Flattened())
    assert reply['mode'] == 'local-model-grounded'
    assert reply['citations'][0]['text'] == document['text']
    assert reply['citations'][0]['text'] in document['text']


def test_explanation_rejects_unverified_sections_and_fabricated_references():
    class Explained(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Replace filter every six months.'}], 'sections': [
                {'heading': 'Schedule', 'text': 'The filter replacement interval is six months.', 'evidence': [0]},
                {'heading': 'Invented', 'text': 'The filter costs $500.', 'evidence': [0]},
                {'heading': 'Wrong reference', 'text': 'Lifetime warranty.', 'evidence': [99]}]}
        def verify_sections(self, question, sections, evidence):
            assert len(sections) == 2
            assert evidence[0]['text'] == 'Replace filter every six months.'
            return [0]
    result = answer_from_evidence('Explain maintenance.', [row('Replace filter every six months.')], Explained())
    assert result['mode'] == 'local-model-explained'
    assert 'six months' in result['answer'] and '[1]' in result['answer']
    assert '$500' not in result['answer'] and 'Lifetime' not in result['answer']
    assert 'omitted' in result['answer']


def test_explanation_review_failure_preserves_verified_quotes():
    class FailedReview(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Replace filter every six months.'}], 'sections': [
                {'heading': 'Invented', 'text': 'The filter costs $500.', 'evidence': [0]}]}
        def verify_sections(self, *args):
            return []
    result = answer_from_evidence('Explain maintenance.', [row('Replace filter every six months.')], FailedReview())
    assert '$500' not in result['answer']
    assert result['citations'][0]['text'] in result['answer']


def test_structured_table_and_speculation_guard():
    class Table(NoModels):
        def generate(self, *args, **kwargs):
            return {'quotes': [{'index': 0, 'quote': 'Eco 21 W, Boost 71 W.'}], 'sections': [
                {'heading': 'Power', 'text': '', 'table': {'columns': ['Mode', 'Power'], 'rows': [['Eco', '21 W'], ['Boost', '71 W']]}, 'evidence': [0]},
                {'heading': 'Invented purpose', 'text': 'Boost is likely intended for industrial use.', 'evidence': [0]}]}
        def verify_sections(self, question, sections, evidence):
            assert len(sections) == 1
            assert '| Boost | 71 W |' in sections[0]['text']
            return [0]
    reply = answer_from_evidence('Compare modes.', [row('Eco 21 W, Boost 71 W.')], Table())
    assert '| Boost | 71 W |' in reply['answer']
    assert 'industrial' not in reply['answer']
