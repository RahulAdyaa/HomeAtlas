from copy import deepcopy
import pytest
from worker.search.common import normalize, Hit, CONFIG
from worker.search.fusion import fuse, retrieve
from worker.search import fuzzy, word
from worker.search.cache import guard, key
from worker.search.suggestions import suggest
from worker.retrieval import unrelated_query

class NoEngine:
    text_identity='none'
    def embed_text(self,*args,**kwargs):return None
    def rerank(self,*args):raise AssertionError('Reranker must be behind flag')

def doc(id,text,path='Study > Desk > Top drawer',**kw):
    return dict(id=id,text=text,title='',location_path=path,**kw)

@pytest.mark.parametrize('query',['Adhaar','Aadhar','Aadhaar','AAADHAAR','adhar card','AAADHAAAR','UID card','आधार'])
def test_aliases(query):assert normalize(query)=='aadhaar'

def test_numbers_preserved():
    assert '00001111' in normalize('serial 00001111')
    assert key('model AAA100')!=key('model AA100')

def test_rrf_dedup_weights():
    c=deepcopy(CONFIG);c['weights']['word']=2
    scores=fuse({'word':[Hit('a',4),Hit('a',3)],'fuzzy':[Hit('a',.8),Hit('b',.7)]},c)
    assert scores['a']==pytest.approx(3/61)
    assert scores['b']==pytest.approx(1/62)

def test_fuzzy_edits_and_no_guess():
    docs=[doc('a','Passport identity record'),doc('b','Fridge warranty')]
    assert fuzzy.search('paspsort',docs)[0].id=='a'
    assert retrieve('quantum unicorn plutonium',docs,NoEngine())==[]

def test_metadata_and_location_boost():
    docs=[doc('a','record',title_override=''),doc('b','record','Kitchen')]
    docs[0]['metadata']={'tags':['aadhaar']}
    assert word.search('aadhaar',docs)[0].id=='a'
    assert retrieve('record study',docs,NoEngine())[0]['id']=='a'

@pytest.mark.parametrize('a,b',[
 ('Where is my passport?','Where is my passport photo?'),
 ('fridge warranty','washing machine warranty'),
 ('passport study','passport bedroom'),('model AB123','model AB124'),
 ('aadhaar number','aadhaar location'),('serial 000012','serial 12'),
 ('pan card','pen card'),('passport','passport sample')])
def test_near_miss_guard(a,b):assert not guard(a,b)

def test_guard_typo_and_paraphrase():
    assert guard('where is my aadhar card','please locate my Aadhaar')
    assert guard('find my paspsort','where is passport')

def test_suggestions_only_low_score():
    docs=[doc('p','passport')]
    assert suggest('passprt',docs,[{'fusion_score':.05}]) is None
    assert suggest('passprt',docs,[])=='passport'

def test_unrelated_lexical_overlap_abstains_before_generation():
    candidate=doc('birth','Birth certificate registration BC-5555')
    assert unrelated_query('dinosaur DNA certificate',[candidate])
    assert not unrelated_query('Where is my birth certificate?',[candidate])


def test_cache_intent_and_serial_phrasing():
    assert guard('What is my Aadhaar card serial number?', 'Show me the serial number of my Aadhar card')
    assert not guard('what is a passport', 'where is passport')
