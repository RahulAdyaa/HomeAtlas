"""Real PostgreSQL regressions, using disposable fictional households only."""
import os
import uuid
from copy import deepcopy
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import pytest
from test_worker_db import database, create_source
from test_semantic_cache import answer
from worker.search.common import CONFIG
from worker.search.postgres import channel, params
from worker.search.cache import lookup, store

pytestmark=pytest.mark.skipif(os.getenv('HOMEATLAS_DB_TESTS')!='1',reason='Opt-in disposable PostgreSQL fixtures')

class Engine:
    text_identity='cache-test';image_identity='vision-fixer-test'
    def embed_text(self,texts,**kwargs):return [[1.,0.,0.] for _ in texts]
    def embed_image_space(self,**kwargs):return [1.,0.]

def test_sql_visual_shortlist_is_diverse_before_limit(database):
    chunk=create_source(database,0,'A short OCR label')
    context,other=uuid.uuid4(),uuid.uuid4()
    with psycopg.connect(database.cfg.database_url,row_factory=dict_row) as c:
        original=c.execute('SELECT * FROM chunks WHERE id=%s',(chunk,)).fetchone()
        c.execute('UPDATE chunks SET page=1,image_path=%s,image_embedding=%s,image_embedding_model=%s WHERE id=%s',
                  ('fictional-page-a.png',[1.,0.],Engine.image_identity,chunk))
        for index in range(35):
            c.execute('''INSERT INTO chunks(id,household_id,source_id,version_id,text,page,image_path,image_embedding,image_embedding_model)
                       VALUES(%s,%s,%s,%s,%s,1,%s,%s,%s)''',
                      (uuid.uuid4(),original['household_id'],original['source_id'],original['version_id'],'Repeated OCR label',
                       'fictional-page-a.png',[1.,0.],Engine.image_identity))
        for id,path,text,meta in [(context,'fictional-page-a.png','Complete OCR labels and values',{'ocr_context':True}),
                                   (other,'fictional-page-b.png','Independent visual page',{})]:
            c.execute('''INSERT INTO chunks(id,household_id,source_id,version_id,text,page,image_path,image_embedding,image_embedding_model,metadata)
                         VALUES(%s,%s,%s,%s,%s,1,%s,%s,%s,%s)''',
                      (id,original['household_id'],original['source_id'],original['version_id'],text,path,[1.,0.],Engine.image_identity,Jsonb(meta)))
    config=deepcopy(CONFIG);config['channel_top_k']=2
    scope=params(str(database.households[0]),database.users[0],'visual labels',None,None)
    hits,rows=channel('visual','visual labels',scope,database.cfg,Engine(),config)
    assert {hit.id for hit in hits}=={str(context),str(other)}
    assert len(rows)==2

def test_sql_numeric_multi_record_and_single_identifier_filters(database):
    first=create_source(database,0,'Unit T1 warranty duration 18 months')
    second=create_source(database,0,'Unit T4 warranty duration 36 months')
    create_source(database,0,'Unit T10 warranty duration 90 months')
    for query,expected in [('Give warranty durations for units T1 and T4',{str(first),str(second)}),
                           ('T1 warranty',{str(first)}),('serial 1234 5678',set())]:
        hits,_=channel('word',query,params(str(database.households[0]),database.users[0],query,None,None),database.cfg,Engine())
        assert {hit.id for hit in hits}==expected

def test_sensitive_card_answer_never_stored_and_legacy_entry_is_purged(database):
    chunk=create_source(database,0,'Fictional appliance model FR-900')
    h,u=str(database.households[0]),database.users[0];engine=Engine()
    benign=lookup(h,u,'fridge model','',database.cfg,engine)
    assert store(h,u,'fridge model','',benign['dataVersion'],answer(database,chunk),50,database.cfg,engine)
    query='What is my Evaluation card serial number?'
    private=dict(answer(database,chunk),answer='Evaluation card serial number: SYNTHETIC-ALPHA-741')
    with psycopg.connect(database.cfg.database_url) as c:
        c.execute('UPDATE answer_cache SET query=%s,answer=%s WHERE household_id=%s AND user_id=%s',(query,Jsonb(private),h,u))
    miss=lookup(h,u,query,'',database.cfg,engine)
    assert not miss['hit'] and miss['bypassReason']=='sensitive-identifier'
    assert not store(h,u,query,'',miss['dataVersion'],private,50,database.cfg,engine)
    with psycopg.connect(database.cfg.database_url) as c:
        assert c.execute('SELECT count(*) FROM answer_cache WHERE household_id=%s AND user_id=%s',(h,u)).fetchone()[0]==0

def test_populated_nonsensitive_cache_remains_user_and_household_scoped(database):
    chunk=create_source(database,0,'Fridge model FR-900')
    h,u=str(database.households[0]),database.users[0];engine=Engine();query='What model is my fridge?'
    miss=lookup(h,u,query,'',database.cfg,engine)
    assert store(h,u,query,'',miss['dataVersion'],answer(database,chunk),50,database.cfg,engine)
    assert lookup(h,u,query,'',database.cfg,engine)['kind']=='exact'
    with psycopg.connect(database.cfg.database_url) as c:
        c.execute("INSERT INTO memberships(household_id,user_id,role) VALUES(%s,%s,'viewer')",(h,database.users[1]))
    assert not lookup(h,database.users[1],query,'',database.cfg,engine)['hit']
    assert not lookup(str(database.households[1]),database.users[1],query,'',database.cfg,engine)['hit']
