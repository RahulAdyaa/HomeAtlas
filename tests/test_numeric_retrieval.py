"""Single identifiers stay exact; explicit multi-record comparisons can span chunks."""
from worker.search.fusion import retrieve
from worker.retrieval import rank_candidates

class Engine:
    def embed_text(self, *args, **kwargs): return None
    def embed_image_space(self, **kwargs): return None

RECORDS = [dict(id='first', text='Mode T1 uses 21 watts.'),
           dict(id='second', text='Mode T4 uses 71 watts.'),
           dict(id='wrong', text='Mode T10 uses 90 watts.')]

def test_explicit_comparison_can_find_each_numeric_record():
    for retrieve_fn in [retrieve, rank_candidates]:
        assert {d['id'] for d in retrieve_fn('Compare power for T1 and T4', RECORDS, Engine())} == {'first', 'second'}

def test_single_identifier_stays_exact_and_multi_part_number_requires_all_parts():
    for retrieve_fn in [retrieve, rank_candidates]:
        assert [d['id'] for d in retrieve_fn('T1 power', RECORDS, Engine())] == ['first']
        assert retrieve_fn('serial 1234 5678', [dict(id='partial', text='serial 1234 7777')], Engine()) == []
