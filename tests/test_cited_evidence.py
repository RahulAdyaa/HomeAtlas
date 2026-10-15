"""Review and display only evidence a supported answer actually uses."""
import json
from types import SimpleNamespace
from worker.models import LocalModels
from worker.retrieval import answer_from_evidence


def row(key,text,**extra):
    return dict(id=key,source_id='source-'+key,version_id='version-'+key,title=key,
                text=text,page=int(key),bbox=[1,2,3,4],metadata={},**extra)


RECORDS=[row('1','Fridge warranty ends in May 2028.'),
         row('2','Unrelated scanned pump pressure is 3 bar.',image_path='unused-scan.png'),
         row('3','Fridge model FR-900 is recorded.')]


def test_review_excludes_unused_visual_quotes_and_keeps_original_indices():
    class Engine:
        def generate(self,*args,**kwargs):
            return {'quotes':[{'index':i,'quote':r['text']} for i,r in enumerate(RECORDS)],
                    'sections':[{'heading':'Model','text':'The fridge model is FR-900.','evidence':[2]}]}
        def verify_sections(self,question,sections,evidence):
            assert sections[0]['evidence']==[2]
            assert [r['index'] for r in evidence]==[2]
            assert all(not r.get('image_path') for r in evidence)
            return [0]
    answer=answer_from_evidence('What model is my fridge?',RECORDS,Engine())
    assert '[1]' in answer['answer'] and '[3]' not in answer['answer']
    assert [(c['id'],c['number'],c['page'],c['bbox']) for c in answer['citations']]==[('3',1,3,[1,2,3,4])]
    assert answer['citations'][0]['sourceId']=='source-3'
    assert answer['citations'][0]['versionId']=='version-3'


def test_multiple_accepted_sections_renumber_only_used_citations():
    class Engine:
        def generate(self,*args,**kwargs):
            return {'quotes':[{'index':i,'quote':r['text']} for i,r in enumerate(RECORDS)],
                    'sections':[{'heading':'Model','text':'Model FR-900.','evidence':[2]},
                                {'heading':'Warranty','text':'Ends May 2028.','evidence':[0]},
                                {'heading':'Wrong','text':'A fictional unsupported number.','evidence':[1]}]}
        def verify_sections(self,*args):return [0,1]
    answer=answer_from_evidence('Give the fridge model and warranty.',RECORDS,Engine())
    assert [(c['id'],c['number']) for c in answer['citations']]==[('1',1),('3',2)]
    assert 'Model FR-900.\n\n[2]' in answer['answer']
    assert 'Ends May 2028.\n\n[1]' in answer['answer']
    assert 'unsupported number' not in answer['answer']


def test_rejected_fabricated_quote_positions_do_not_corrupt_citation_mapping():
    class Engine:
        def generate(self,*args,**kwargs):
            return {'quotes':[{'index':0,'quote':'A fabricated value never in source.'},
                              {'index':1,'quote':RECORDS[1]['text']},
                              {'index':2,'quote':RECORDS[2]['text']}],
                    'sections':[{'heading':'Model','text':'Model FR-900.','evidence':[2]}]}
        def verify_sections(self,question,sections,evidence):
            assert sections[0]['evidence']==[1]
            assert [r['index'] for r in evidence]==[1]
            return [0]
    answer=answer_from_evidence('What is the fridge model?',RECORDS,Engine())
    assert [(c['id'],c['number']) for c in answer['citations']]==[('3',1)]
    assert '[1]' in answer['answer']


def test_local_verifier_payload_omits_unreferenced_images(monkeypatch):
    captured=[]
    def attachments(evidence,cfg,question):
        assert [r['index'] for r in evidence]==[2]
        assert all(not r.get('image_path') for r in evidence)
        return [],''
    def urlopen(request,timeout):
        captured.append(json.loads(request.data))
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'message':{'content':'{"supported":[0]}'}}).encode()
        return Response()
    monkeypatch.setattr('worker.vision_assets.attachments',attachments)
    monkeypatch.setattr('worker.models.urlopen',urlopen)
    engine=LocalModels(SimpleNamespace(generation_model='qwen3-vl:4b-instruct',ollama_url='http://127.0.0.1:11434'))
    assert engine.verify_sections('Fridge model?', [{'text':'FR-900','evidence':[2]}],
                                  [dict(r,index=i) for i,r in enumerate(RECORDS)])==[0]
    payload=json.loads(captured[0]['messages'][1]['content'])
    assert payload['quotes']==[{'index':2,'text':RECORDS[2]['text'],'page':3}]
    assert 'images' not in captured[0]['messages'][1]


def test_referenced_visual_quote_keeps_its_image_and_nonzero_index(monkeypatch):
    captured=[]
    def attachments(evidence,cfg,question):
        assert [r['index'] for r in evidence]==[1]
        assert evidence[0]['image_path']=='unused-scan.png'
        return ['synthetic-image-payload'],'Attached source image 1 belongs to indices [1].'
    def urlopen(request,timeout):
        captured.append(json.loads(request.data))
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return b'{"message":{"content":"{\\"supported\\":[0]}"}}'
        return Response()
    monkeypatch.setattr('worker.vision_assets.attachments',attachments)
    monkeypatch.setattr('worker.models.urlopen',urlopen)
    engine=LocalModels(SimpleNamespace(generation_model='qwen3-vl:4b-instruct',ollama_url='http://127.0.0.1:11434'))
    assert engine.verify_sections('Read the pump pressure.',[{'text':'3 bar','evidence':[1]}],
                                  [dict(r,index=i) for i,r in enumerate(RECORDS)])==[0]
    assert captured[0]['messages'][1]['images']==['synthetic-image-payload']
    assert 'indices [1]' in captured[0]['messages'][1]['content']
