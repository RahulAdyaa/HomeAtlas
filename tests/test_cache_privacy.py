"""Synthetic identifier policy; no real card values are used."""
import pytest
from worker.search.cache import sensitive_identifier

@pytest.mark.parametrize('query',[
 'What is my Evaluation card serial number?',
 'What is my Aadhaar number?', 'Tell me my PAN identifier',
 'What is my passport number?', 'Driving licence serial number',
 'आधार number',
])
def test_personal_identifier_queries_bypass(query):
    assert sensitive_identifier(query)

@pytest.mark.parametrize('query',['Where is my passport?', 'Where is my Aadhaar card?',
 'What model is my fridge?', 'What is my appliance serial number?'])
def test_non_identifier_locations_and_appliance_models_can_be_cached(query):
    assert not sensitive_identifier(query)

def test_generic_question_cannot_hide_personal_identifier_in_answer_or_citation():
    assert sensitive_identifier('What is recorded?', {'answer':'Evaluation card — Serial number: SYNTHETIC-ALPHA-741'})
    assert sensitive_identifier('What is recorded?', {'answer':'See record', 'citations':[{'text':'PAN identifier: SYNTHETIC-PAN-ALPHA'}]})
    assert sensitive_identifier('Show details', {'recordFacts':[{'name':'Fictional card','field':'serialNumber','label':'Serial number','value':'SYNTHETIC-ALPHA-741'}]})
