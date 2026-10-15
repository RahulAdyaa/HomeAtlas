"""Durable leased jobs: publish immutable evidence and settle credits in one transaction."""
from dataclasses import asdict
import hashlib
import json
import logging
from pathlib import Path
import threading
import time
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import Settings, settings
from .ingestion import extract
from .models import LocalModels, models

log = logging.getLogger('homeatlas.jobs')


def connect(cfg: Settings = settings):
    return psycopg.connect(cfg.database_url, row_factory=dict_row)


def claim_job(cfg: Settings = settings) -> dict | None:
    with connect(cfg) as conn:
        job = conn.execute('''SELECT * FROM ingestion_jobs
            WHERE status='queued' OR (status='processing' AND COALESCE(heartbeat_at,started_at,created_at) < now() - make_interval(secs=>%s))
            ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1''', (cfg.lease_seconds,)).fetchone()
        if not job:
            return None
        if job['attempts'] >= cfg.max_attempts:
            conn.execute("UPDATE ingestion_jobs SET status='failed',error='Worker retry limit reached',completed_at=now() WHERE id=%s", (job['id'],))
            conn.execute("UPDATE sources SET status='failed' WHERE id=%s AND household_id=%s AND current_version_id=%s", (job['source_id'], job['household_id'], job['version_id']))
            conn.execute('SELECT atlas_settle_credit(%s,%s,false)', (job['household_id'], job['operation_id']))
            return None
        job['claim_token'] = uuid.uuid4()
        job['attempts'] += 1
        conn.execute("UPDATE ingestion_jobs SET status='processing',attempts=%s,claim_token=%s,started_at=now(),heartbeat_at=now(),error=NULL WHERE id=%s",
                     (job['attempts'], job['claim_token'], job['id']))
        conn.execute("UPDATE sources SET status='processing' WHERE id=%s AND household_id=%s AND current_version_id=%s", (job['source_id'], job['household_id'], job['version_id']))
        return job


def heartbeat(job: dict, done: threading.Event, cfg: Settings):
    while not done.wait(20):
        try:
            with connect(cfg) as conn:
                conn.execute("UPDATE ingestion_jobs SET heartbeat_at=now() WHERE id=%s AND claim_token=%s AND status='processing'", (job['id'], job['claim_token']))
        except Exception:
            log.warning('job_heartbeat_failed job=%s', job['id'])


def job_source(conn, job: dict) -> dict:
    source = conn.execute('''SELECT v.*,s.room_id,s.item_id,s.location_id,s.location_path,m.role FROM source_versions v
        JOIN sources s ON s.id=v.source_id AND s.household_id=v.household_id
        JOIN memberships m ON m.household_id=v.household_id AND m.user_id=%s
        WHERE v.id=%s AND v.household_id=%s AND v.source_id=%s AND m.role IN ('owner','editor') FOR SHARE OF s''',
        (job['actor_id'], job['version_id'], job['household_id'], job['source_id'])).fetchone()
    if not source:
        raise PermissionError('Upload permission was removed or source no longer exists')
    return source


def process_job(job: dict, cfg: Settings = settings, engine: LocalModels = models):
    done = threading.Event()
    thread = threading.Thread(target=heartbeat, args=(job, done, cfg), daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        with connect(cfg) as conn:
            source = job_source(conn, job)
        path = cfg.private_path(source['storage_path'])
        with path.open('rb') as original:
            digest = hashlib.file_digest(original, 'sha256').hexdigest()
        if digest != source['sha256']:
            raise ValueError('Original file integrity check failed')
        artifacts = cfg.storage / 'derived' / str(job['household_id']) / str(job['version_id']) / str(job['claim_token'])
        chunks = extract(path, source['mime_type'], artifacts, cfg)
        for chunk in chunks:
            chunk.metadata['content_text'] = chunk.text
            chunk.text = f"Location: {source['location_path']}\n\n{chunk.text}"
        embeddings = engine.embed_text([chunk.text for chunk in chunks])
        image_vectors = {}
        for chunk in chunks:
            if chunk.image_path and chunk.image_path not in image_vectors:
                image_vectors[chunk.image_path] = engine.embed_image_space(image=Path(chunk.image_path))
        with connect(cfg) as conn:
            lease = conn.execute("SELECT id FROM ingestion_jobs WHERE id=%s AND claim_token=%s AND status='processing' FOR UPDATE", (job['id'], job['claim_token'])).fetchone()
            if not lease:
                return  # A reclaimed worker owns this job; it alone may publish or settle.
            current = job_source(conn, job)  # Lock attachment through publication.
            if current['location_path'] != source['location_path'] or current['location_id'] != source['location_id']:
                source = current
                for chunk in chunks:
                    chunk.text = f"Location: {source['location_path']}\n\n{chunk.metadata['content_text']}"
                embeddings = engine.embed_text([chunk.text for chunk in chunks])
            # Old rows remain addressable by saved citations, while only this index generation is searched.
            conn.execute("UPDATE chunks SET metadata=jsonb_set(metadata,'{active}','false'::jsonb) WHERE household_id=%s AND version_id=%s", (job['household_id'], job['version_id']))
            for index, chunk in enumerate(chunks):
                fingerprint = json.dumps([index, chunk.text, chunk.page, chunk.bbox, chunk.start_seconds, chunk.end_seconds, chunk.modality])
                chunk_id = uuid.uuid5(uuid.UUID(str(job['version_id'])), fingerprint)
                image_vector = image_vectors.get(chunk.image_path)
                metadata = dict(chunk.metadata, source_sha256=source['sha256'], source_version=source['version'],
                                location_id=str(source['location_id']), location_path=source['location_path'], permissions='household-members', extractor_version='homeatlas-2-image-evidence', active=True)
                conn.execute('''INSERT INTO chunks(id,household_id,source_id,version_id,item_id,room_id,text,page,bbox,
                    start_seconds,end_seconds,modality,embedding,embedding_model,model_revision,image_path,metadata,image_embedding,image_embedding_model)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                    embedding=EXCLUDED.embedding,embedding_model=EXCLUDED.embedding_model,model_revision=EXCLUDED.model_revision,
                    image_embedding=EXCLUDED.image_embedding,image_embedding_model=EXCLUDED.image_embedding_model,
                    metadata=EXCLUDED.metadata''',
                    (chunk_id, job['household_id'], job['source_id'], job['version_id'], source['item_id'], source['room_id'],
                     chunk.text, chunk.page, Jsonb(chunk.bbox) if chunk.bbox else None, chunk.start_seconds, chunk.end_seconds,
                     chunk.modality, embeddings[index] if embeddings else None, engine.text_identity if embeddings else None,
                     engine.cfg.text_revision if embeddings else None, chunk.image_path, Jsonb(metadata), image_vector,
                     engine.image_identity if image_vector else None))
            conn.execute("UPDATE ingestion_jobs SET status='ready',completed_at=now(),heartbeat_at=now() WHERE id=%s", (job['id'],))
            conn.execute("UPDATE sources SET status='ready' WHERE id=%s AND household_id=%s AND current_version_id=%s", (job['source_id'], job['household_id'], job['version_id']))
            conn.execute('SELECT atlas_settle_credit(%s,%s,true)', (job['household_id'], job['operation_id']))
            conn.execute("INSERT INTO audit_events(household_id,actor_id,action,target_id,metadata) VALUES(%s,%s,'source.ready',%s,%s)",
                         (job['household_id'], job['actor_id'], str(job['source_id']), Jsonb({'chunks': len(chunks), 'versionId': str(job['version_id'])})))
        log.info('job_ready job=%s chunks=%d elapsed_ms=%d', job['id'], len(chunks), int((time.monotonic() - started) * 1000))
    except Exception as exc:
        # Only intentional validation messages are retained; arbitrary model/library errors can contain source text.
        public_error = str(exc)[:300] if type(exc) in (ValueError, PermissionError) else 'Processing failed; inspect the private worker runtime and retry'
        with connect(cfg) as conn:
            lease = conn.execute("SELECT id FROM ingestion_jobs WHERE id=%s AND claim_token=%s AND status='processing' FOR UPDATE", (job['id'], job['claim_token'])).fetchone()
            if lease:
                conn.execute("UPDATE ingestion_jobs SET status='failed',error=%s,completed_at=now() WHERE id=%s", (public_error, job['id']))
                conn.execute("UPDATE sources SET status='failed' WHERE id=%s AND household_id=%s AND current_version_id=%s", (job['source_id'], job['household_id'], job['version_id']))
                conn.execute('SELECT atlas_settle_credit(%s,%s,false)', (job['household_id'], job['operation_id']))
        log.warning('job_failed job=%s error=%s', job['id'], type(exc).__name__)
    finally:
        done.set()
        thread.join(timeout=2)


def refresh_location_embeddings(cfg: Settings, engine: LocalModels = models):
    # Compare-and-swap prevents a rename during inference publishing an outdated vector.
    with connect(cfg) as conn:
        rows = conn.execute("SELECT id,text FROM chunks WHERE metadata->>'location_embedding_pending'='true' OR embedding_model IS DISTINCT FROM %s LIMIT 32", (engine.text_identity,)).fetchall()
    if not rows:
        return
    vectors = engine.embed_text([r['text'] for r in rows])
    if not vectors:
        return
    with connect(cfg) as conn:
        for row, vector in zip(rows, vectors):
            conn.execute("UPDATE chunks SET embedding=%s,embedding_model=%s,model_revision=%s,metadata=metadata-'location_embedding_pending' WHERE id=%s AND text=%s", (vector, engine.text_identity, engine.cfg.text_revision, row['id'], row['text']))


def run(stop: threading.Event, cfg: Settings = settings):
    while not stop.is_set():
        try:
            refresh_location_embeddings(cfg)
            job = claim_job(cfg)
            if job:
                process_job(job, cfg)
                continue
        except Exception as exc:
            log.warning('queue_iteration_failed error=%s', type(exc).__name__)
        stop.wait(2)
