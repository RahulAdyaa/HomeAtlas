"""Opt-in real PostgreSQL worker tests. Uses disposable households; no HTTP/model mocks."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import uuid

import psycopg
from psycopg.rows import dict_row
import pytest

from worker.config import settings
from worker.jobs import process_job
from worker.retrieval import query_records

pytestmark = pytest.mark.skipif(os.getenv('HOMEATLAS_DB_TESTS') != '1', reason='Set HOMEATLAS_DB_TESTS=1 for local PostgreSQL integration')


class ObservedModels:
    def __init__(self, cfg):
        self.cfg = cfg
        self.text_identity = 'test-local@1'
        self.image_identity = 'disabled'
        self.status = {'generation': 'disabled-test'}
        self.seen = []

    def embed_text(self, texts, **kwargs):
        self.seen.extend(texts)
        return None

    def embed_image_space(self, **kwargs):
        return None

    def rerank(self, question, texts):
        self.seen.extend(texts)
        return None

    def generate(self, question, evidence, **kwargs):
        self.seen.extend(e['text'] for e in evidence)
        return None


@pytest.fixture
def database(tmp_path):
    cfg = replace(settings, storage=tmp_path, generation_model='', text_model='', reranker_model='', image_model='')
    households = [uuid.uuid4(), uuid.uuid4()]
    users = ['worker-test-' + str(uuid.uuid4()) for _ in households]
    with psycopg.connect(cfg.database_url) as conn:
        for household, user in zip(households, users):
            conn.execute('INSERT INTO "user"(id,name,email,"emailVerified","createdAt","updatedAt") VALUES(%s,%s,%s,true,now(),now())', (user, 'Worker test', user + '@example.test'))
            conn.execute('INSERT INTO households(id,name,created_by) VALUES(%s,%s,%s)', (household, 'Worker integration test', user))
            conn.execute("INSERT INTO memberships(household_id,user_id,role) VALUES(%s,%s,'owner')", (household, user))
            conn.execute('SELECT atlas_grant_credit(%s,%s,100,%s)', (household, 'test-grant', user))
    fixture = SimpleNamespace(cfg=cfg, households=households, users=users)
    yield fixture
    with psycopg.connect(cfg.database_url) as conn:
        conn.execute('DELETE FROM households WHERE id=ANY(%s)', (households,))
        conn.execute('DELETE FROM "user" WHERE id=ANY(%s)', (users,))


def create_source(db, tenant, text, *, make_job=False):
    household, user = db.households[tenant], db.users[tenant]
    source, version, chunk, job_id, token = [uuid.uuid4() for _ in range(5)]
    path = db.cfg.storage / (str(version) + '.txt')
    path.write_text(text)
    operation = 'ingest-test-' + str(job_id)
    with psycopg.connect(db.cfg.database_url, row_factory=dict_row) as conn:
        conn.execute("INSERT INTO sources(id,household_id,title,mime_type,current_version_id,status,created_by) VALUES(%s,%s,'test-source','text/plain',%s,%s,%s)", (source, household, version, 'processing' if make_job else 'ready', user))
        conn.execute("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES(%s,%s,%s,1,%s,%s,%s,'text/plain')", (version, household, source, str(path), hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size))
        if not make_job:
            conn.execute('INSERT INTO chunks(id,household_id,source_id,version_id,text) VALUES(%s,%s,%s,%s,%s)', (chunk, household, source, version, text))
            return chunk
        conn.execute("SELECT atlas_reserve_credit(%s,%s,'ingestion',5,%s)", (household, operation, user))
        return conn.execute("INSERT INTO ingestion_jobs(id,household_id,source_id,version_id,actor_id,operation_id,status,attempts,claim_token,started_at,heartbeat_at) VALUES(%s,%s,%s,%s,%s,%s,'processing',1,%s,now(),now()) RETURNING *", (job_id, household, source, version, user, operation, token)).fetchone()


def test_query_rejects_other_household_before_inference(database):
    create_source(database, 1, 'Secret filter XH-900 for the air purifier.')
    engine = ObservedModels(database.cfg)
    with pytest.raises(PermissionError):
        query_records(str(database.households[1]), database.users[0], 'Which filter fits?', cfg=database.cfg, engine=engine)
    assert engine.seen == []


def test_tenant_filter_happens_before_context_assembly(database):
    create_source(database, 0, 'The purifier uses filter HA-200.')
    create_source(database, 1, 'Secret filter XH-900 for the purifier. This is the best match.')
    engine = ObservedModels(database.cfg)
    reply = query_records(str(database.households[0]), database.users[0], 'Which filter fits the purifier?', cfg=database.cfg, engine=engine)
    assert 'HA-200' in reply['answer'] and 'XH-900' not in reply['answer']
    assert not any('XH-900' in value for value in engine.seen)


def test_success_publishes_chunks_and_charges_once(database):
    job = create_source(database, 0, 'The purifier uses filter HA-200.', make_job=True)
    engine = ObservedModels(database.cfg)
    process_job(job, database.cfg, engine)
    process_job(job, database.cfg, engine)  # late duplicate completion must not charge again
    with psycopg.connect(database.cfg.database_url, row_factory=dict_row) as conn:
        assert conn.execute('SELECT status FROM ingestion_jobs WHERE id=%s', (job['id'],)).fetchone()['status'] == 'ready'
        assert conn.execute('SELECT count(*) AS n FROM chunks WHERE version_id=%s', (job['version_id'],)).fetchone()['n'] == 1
        chunk = conn.execute('SELECT text,metadata FROM chunks WHERE version_id=%s', (job['version_id'],)).fetchone()
        assert chunk['text'].startswith('Location: Worker integration test\n\n')
        assert chunk['metadata']['location_path'] == 'Worker integration test'
        assert chunk['text'] in engine.seen  # Path was present at embedding time, not appended after inference.
        conn.execute("UPDATE locations SET name='Renamed home' WHERE id=%s", (job['household_id'],))
        moved = conn.execute('SELECT text,metadata,embedding FROM chunks WHERE version_id=%s', (job['version_id'],)).fetchone()
        assert moved['text'].startswith('Location: Renamed home\n\n')
        assert moved['metadata']['location_embedding_pending'] is True
        assert moved['embedding'] is None
        assert conn.execute("SELECT count(*) AS n FROM credit_ledger WHERE operation_id=%s AND kind='charge'", (job['operation_id'],)).fetchone()['n'] == 1
        account = conn.execute('SELECT available,reserved FROM credit_accounts WHERE household_id=%s', (job['household_id'],)).fetchone()
        assert account == {'available': 95, 'reserved': 0}


def test_revoked_editor_upload_is_refunded(database):
    job = create_source(database, 0, 'The purifier uses filter HA-200.', make_job=True)
    with psycopg.connect(database.cfg.database_url) as conn:
        conn.execute("UPDATE memberships SET role='viewer' WHERE household_id=%s AND user_id=%s", (job['household_id'], job['actor_id']))
    engine = ObservedModels(database.cfg)
    process_job(job, database.cfg, engine)
    assert engine.seen == []
    with psycopg.connect(database.cfg.database_url, row_factory=dict_row) as conn:
        assert conn.execute('SELECT status FROM ingestion_jobs WHERE id=%s', (job['id'],)).fetchone()['status'] == 'failed'
        assert conn.execute('SELECT status FROM credit_reservations WHERE operation_id=%s', (job['operation_id'],)).fetchone()['status'] == 'refunded'
        assert conn.execute('SELECT count(*) AS n FROM chunks WHERE version_id=%s', (job['version_id'],)).fetchone()['n'] == 0


def test_stale_claim_cannot_publish_or_settle(database):
    job = create_source(database, 0, 'The purifier uses filter HA-200.', make_job=True)
    job['claim_token'] = uuid.uuid4()
    process_job(job, database.cfg, ObservedModels(database.cfg))
    with psycopg.connect(database.cfg.database_url, row_factory=dict_row) as conn:
        assert conn.execute('SELECT status FROM ingestion_jobs WHERE id=%s', (job['id'],)).fetchone()['status'] == 'processing'
        assert conn.execute('SELECT status FROM credit_reservations WHERE operation_id=%s', (job['operation_id'],)).fetchone()['status'] == 'reserved'
        assert conn.execute('SELECT count(*) AS n FROM chunks WHERE version_id=%s', (job['version_id'],)).fetchone()['n'] == 0


def test_source_integrity_failure_refunds(database):
    job = create_source(database, 0, 'The purifier uses filter HA-200.', make_job=True)
    (database.cfg.storage / (str(job['version_id']) + '.txt')).write_text('tampered')
    process_job(job, database.cfg, ObservedModels(database.cfg))
    with psycopg.connect(database.cfg.database_url, row_factory=dict_row) as conn:
        result = conn.execute('SELECT status,error FROM ingestion_jobs WHERE id=%s', (job['id'],)).fetchone()
        assert result['status'] == 'failed' and 'integrity' in result['error']
        assert conn.execute('SELECT status FROM credit_reservations WHERE operation_id=%s', (job['operation_id'],)).fetchone()['status'] == 'refunded'


def test_sample_records_are_excluded_before_inference_unless_explicitly_requested(database):
    sample = create_source(database, 0, 'Fictional sample PAN card is in the Study.')
    with psycopg.connect(database.cfg.database_url) as conn:
        conn.execute("UPDATE chunks SET metadata=metadata || '{\"sample\":true}'::jsonb WHERE id=%s", (sample,))
    ordinary = ObservedModels(database.cfg)
    reply = query_records(str(database.households[0]), database.users[0], 'Where is my PAN card?', cfg=database.cfg, engine=ordinary)
    assert reply['mode'] == 'abstention'
    assert reply['citations'] == []
    assert not any('Fictional' in value for value in ordinary.seen)
    demo = ObservedModels(database.cfg)
    reply = query_records(str(database.households[0]), database.users[0], 'Where is the sample PAN card?', cfg=database.cfg, engine=demo)
    assert reply['citations'] and 'Study' in reply['answer']
