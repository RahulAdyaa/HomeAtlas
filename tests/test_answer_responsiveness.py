"""Exact quotations establish provenance, not that an answer addresses the question."""
from worker.retrieval import answer_from_evidence

def row():
    return dict(id='chunk',source_id='source',version_id='version',title='Manual',
                text='Routine service interval is six months.',lexical_score=1)

class Engine:
    def generate(self,*args,**kwargs):
        return {'quotes':[{'index':0,'quote':row()['text']}], 'sections':[], 'insufficient':False}
    def verify_sections(self,question,sections,evidence):
        assert 'serial number' in question
        assert sections[0]['text']==row()['text']
        return []

def test_exact_but_unresponsive_quote_is_not_a_supported_answer():
    result=answer_from_evidence('What is the serial number of my emergency valve?',[row()],Engine())
    assert result['mode']=='abstention' and result['citations']==[]

def test_responsive_quote_only_answer_can_be_independently_approved():
    class Responsive(Engine):
        def verify_sections(self,question,sections,evidence):return [0]
    result=answer_from_evidence('What is the routine service interval?',[row()],Responsive())
    assert result['confidence']=='supported' and result['citations'][0]['text']==row()['text']
