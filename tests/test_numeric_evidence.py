"""Literal grounding is conservative; it does not validate arbitrary arithmetic."""
import json
from types import SimpleNamespace
import pytest
from worker.numeric_evidence import literals,supported_literals
from worker.models import LocalModels


def section(text,refs=None):return {'text':text,'evidence':refs or [0]}
def quote(text,index=0,**extra):return dict(index=index,text=text,**extra)


def test_supported_direct_value_and_unsupported_substitution():
    evidence=[quote('Unit T1 warranty is 18 months.')]
    assert supported_literals(section('Unit T1 warranty is 18 months.'),evidence)
    assert not supported_literals(section('Unit T1 warranty is 99 months.'),evidence)


def test_only_this_sections_cited_values_count():
    evidence=[quote('Unit T1 warranty is 18 months.'),quote('Unit T4 warranty is 36 months.',1)]
    assert supported_literals(section('T1: 18 months; T4: 36 months.',[0,1]),evidence)
    assert not supported_literals(section('T1: 36 months.'),evidence)


@pytest.mark.parametrize('source,answer',[
 ('Fridge model FR-900; serial AB-00001234.','Model FR900; serial AB00001234.'),
 ('Fictional identifier 000012345678.','Fictional identifier 0000 1234 5678.'),
 ('Price is 1,250.00; power is 18 W.','Price: 1250; power: 18W.'),
 ('Inspection date 2026-01-15.','Inspection date 15/01/2026.'),
 ('Warranty lasts 18 months.','Warranty lasts 18.0 months.'),
])
def test_literal_formatting(source,answer):
    assert supported_literals(section(answer),[quote(source)])


def test_identifiers_keep_zeroes_and_values_are_not_fuzzy():
    assert not supported_literals(section('Serial AB1234.'),[quote('Serial AB00001234.')])
    assert not supported_literals(section('Identifier 12345678.'),[quote('Identifier 000012345678.')])
    assert not supported_literals(section('Model T10.'),[quote('Model T1.')])
    assert not supported_literals(section('Serial AB1-234.'),[quote('Serial AB-12-34.')])
    assert not supported_literals(section('Pressure is 18 bar.'),[quote('Pressure is -18 bar.')])


def test_unverified_derived_numbers_abstain_but_direct_literals_can_pass():
    evidence=[quote('T1: 18 months.'),quote('T4: 36 months.',1)]
    assert not supported_literals(section('Combined: 54 months.',[0,1]),evidence)
    assert supported_literals(section('T1: 18 months; T4: 36 months.',[0,1]),evidence)
    # No conversion of number words into invented numeric evidence.
    assert not supported_literals(section('18 months.'),[quote('Eighteen months.')])


def test_referenced_visual_evidence_bypasses_literal_guard_but_unused_image_does_not():
    visual=quote('Chart title.',1,image_path='synthetic.png',metadata={'visual_anchor':True})
    evidence=[quote('Unit T1 warranty 18 months.'),visual]
    assert supported_literals(section('Chart value 99.',[1]),evidence)
    assert not supported_literals(section('T1 warranty 99 months.'),evidence)


def test_unsupported_literal_rejects_before_any_model_http_call(monkeypatch):
    monkeypatch.setattr('worker.models.urlopen',lambda *a,**k:pytest.fail('Unsupported literal must not reach model'))
    engine=LocalModels(SimpleNamespace(generation_model='qwen3-vl:4b-instruct',ollama_url='http://127.0.0.1:11434'))
    assert engine.verify_sections('T1 warranty?',[section('Unit T1 warranty 99 months.')],[quote('Unit T1 warranty 18 months.')])==[]


def test_valid_sections_keep_original_section_indices_after_numeric_rejection(monkeypatch):
    captured=[]
    def urlopen(request,timeout):
        captured.append(json.loads(request.data))
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return b'{"message":{"content":"{\\"supported\\":[0,1]}"}}'
        return Response()
    monkeypatch.setattr('worker.models.urlopen',urlopen)
    engine=LocalModels(SimpleNamespace(generation_model='qwen3-vl:4b-instruct',ollama_url='http://127.0.0.1:11434'))
    assert engine.verify_sections('T1 warranty?',[section('99 months.',[1]),section('18 months.')],
                                  [quote('T1 warranty 18 months.'),quote('Other unit warranty 36 months.',1)])==[1]
    payload=json.loads(captured[0]['messages'][1]['content'])
    assert [s['sectionIndex'] for s in payload['sections']]==[1]
    assert [q['index'] for q in payload['quotes']]==[0]
