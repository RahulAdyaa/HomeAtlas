import uuid
import time
from copy import deepcopy
import psycopg
from psycopg.rows import dict_row
from test_worker_db import database, create_source
from worker.search.cache import lookup, store, clear, CONFIG, guard
from worker.search.common import normalize

class Engine:
    text_identity='cache-test'
    def embed_text(self,texts,**kw):return [[1.,0.,0.] for _ in texts]

def answer(database,chunk):
    with psycopg.connect(database.cfg.database_url,row_factory=dict_row) as c:
        row=c.execute('SELECT c.*,s.location_path FROM chunks c JOIN sources s ON s.id=c.source_id WHERE c.id=%s',(chunk,)).fetchone()
    return {'answer':'Fictional passport record','confidence':'supported','mode':'extractive',
            'citations':[{'id':str(chunk),'sourceId':str(row['source_id']),'versionId':str(row['version_id']),
                          'text':row['text'],'locationPath':row['location_path']}]}

def put(db,q='where is my passport'):
    chunk=create_source(db,0,'Passport is in the Study drawer.')
    h,u=str(db.households[0]),db.users[0];e=Engine()
    miss=lookup(h,u,q,'',db.cfg,e)
    assert store(h,u,q,'',miss['dataVersion'],answer(db,chunk),200,db.cfg,e)
    return h,u,e,chunk

def test_exact_semantic_privacy_and_near_miss(database):
    h,u,e,_=put(database)
    assert lookup(h,u,'where is my passport','',database.cfg,e)['kind']=='exact'
    assert lookup(h,u,'please locate my paspsort','',database.cfg,e)['kind']=='semantic'
    for query in ['passport photo','passport study','passport number','fridge warranty']:
        assert not lookup(h,u,query,'',database.cfg,e)['hit']
    assert not lookup(str(database.households[1]),database.users[1],'where is my passport','',database.cfg,e)['hit']
    assert not lookup(h,u,'where is my passport','room-specific',database.cfg,e)['hit']
    assert not lookup(h,u,'where is my passport','',database.cfg,e,bypass=True)['hit']

def test_move_delete_version_and_reference_validation(database):
    h,u,e,chunk=put(database)
    with psycopg.connect(database.cfg.database_url) as c:
        room=uuid.uuid4()
        c.execute("INSERT INTO rooms(id,household_id,name) VALUES(%s,%s,'Bedroom')",(room,h))
        c.execute('UPDATE sources SET location_id=%s WHERE id=(SELECT source_id FROM chunks WHERE id=%s)',(room,chunk))
    assert not lookup(h,u,'where is my passport','',database.cfg,e)['hit']
    current=lookup(h,u,'where is my passport','',database.cfg,e)
    updated=answer(database,chunk)
    assert 'Bedroom' in updated['citations'][0]['locationPath']
    assert store(h,u,'where is my passport','',current['dataVersion'],updated,200,database.cfg,e)
    assert 'Bedroom' in lookup(h,u,'where is my passport','',database.cfg,e)['answer']['citations'][0]['locationPath']
    with psycopg.connect(database.cfg.database_url) as c:
        c.execute('DELETE FROM sources WHERE id=(SELECT source_id FROM chunks WHERE id=%s)',(chunk,))
    assert not lookup(h,u,'where is my passport','',database.cfg,e)['hit']

def test_stale_store_clear_and_negative_ttl(database):
    h,u,e,chunk=put(database)
    old=lookup(h,u,'where is my passport','',database.cfg,e)['dataVersion']
    clear(h,u,database.cfg)
    assert not store(h,u,'where is my passport','',old,answer(database,chunk),200,database.cfg,e)
    current=lookup(h,u,'unicorn','',database.cfg,e)
    assert store(h,u,'unicorn','',current['dataVersion'],{'answer':"I couldn't find that",'confidence':'insufficient','citations':[]},10,database.cfg,e)
    with psycopg.connect(database.cfg.database_url) as c:
        ttl=c.execute("SELECT extract(epoch FROM expires_at-created_at) FROM answer_cache WHERE household_id=%s",(h,)).fetchone()[0]
        assert 299<=ttl<=301
        c.execute("UPDATE answer_cache SET expires_at=now()-interval '1 second' WHERE household_id=%s",(h,))
    assert not lookup(h,u,'unicorn','',database.cfg,e)['hit']

def test_user_isolation_and_lru(database):
    h,u,e,_=put(database)
    other=database.users[1]
    with psycopg.connect(database.cfg.database_url) as c:
        c.execute("INSERT INTO memberships(household_id,user_id,role) VALUES(%s,%s,'viewer')",(h,other))
    assert not lookup(h,other,'where is my passport','',database.cfg,e)['hit']
    old=CONFIG['cache']['max_entries_per_user'];CONFIG['cache']['max_entries_per_user']=2
    try:
        for q in ['moon','sun','mars']:
            m=lookup(h,u,q,'',database.cfg,e)
            store(h,u,q,'',m['dataVersion'],{'answer':"I couldn't find that",'confidence':'insufficient','citations':[]},20,database.cfg,e)
        with psycopg.connect(database.cfg.database_url) as c:
            assert c.execute('SELECT count(*) FROM answer_cache WHERE household_id=%s',(h,)).fetchone()[0]==2
        assert not lookup(h,u,'moon','',database.cfg,e)['hit']
    finally:CONFIG['cache']['max_entries_per_user']=old

def test_sql_normalization_index_updates_and_version_events(database):
    h,u=str(database.households[0]),database.users[0]
    chunk=create_source(database,0,'Aadhaar DEMO123')
    with psycopg.connect(database.cfg.database_url,row_factory=dict_row) as c:
        for text in ['AAADHAAAR','UID card','Adhaar','passport PHOTO','ＡＡＤＨＡＡＲ','आधार']:
            assert c.execute('SELECT atlas_search_normalize(%s) v',(text,)).fetchone()['v']==normalize(text)
        v=c.execute('SELECT data_version FROM households WHERE id=%s',(h,)).fetchone()['data_version']
        c.execute("UPDATE sources SET title='Passport photograph' WHERE id=(SELECT source_id FROM chunks WHERE id=%s)",(chunk,))
        row=c.execute('SELECT search_text FROM chunks WHERE id=%s',(chunk,)).fetchone()
        assert 'passport photo' in row['search_text']
        assert c.execute('SELECT data_version FROM households WHERE id=%s',(h,)).fetchone()['data_version']>v
        c.execute('UPDATE chunks SET metadata=%s WHERE id=%s',(psycopg.types.json.Jsonb({'tags':['secretlabel']}),chunk))
        assert c.execute("SELECT search_terms @@ to_tsquery('simple','secretlabel') v FROM chunks WHERE id=%s",(chunk,)).fetchone()['v']
