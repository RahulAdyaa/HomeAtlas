from contextlib import asynccontextmanager
import hmac
import logging
import threading
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
import psycopg

from .config import settings
from .ingestion import transcribe, probe_media
from .jobs import run
from .models import models
from .retrieval import query_records

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    if len(settings.worker_key) < 24:
        raise RuntimeError('WORKER_KEY must be a secret with at least 24 characters')
    stop = threading.Event()
    thread = threading.Thread(target=run, args=(stop,), daemon=True)
    thread.start()
    yield
    stop.set()
    thread.join(timeout=5)


app = FastAPI(title='HomeAtlas private worker', docs_url=None, redoc_url=None, lifespan=lifespan)


def authorize(x_worker_key: str = Header(default='')):
    if not settings.worker_key or not hmac.compare_digest(x_worker_key, settings.worker_key):
        raise HTTPException(401, 'Private worker authentication required')


class Query(BaseModel):
    householdId: UUID
    actorId: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=3000)
    itemId: UUID | None = None
    roomId: UUID | None = None
    imagePath: str | None = None


@app.get('/health')
def health():
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.execute('SELECT 1')
        return {'status': 'ok', 'database': 'ok', 'inference': 'self-hosted', 'models': dict(models.status), 'ocr': settings.ocr_backend}
    except Exception:
        raise HTTPException(503, 'Database unavailable')


@app.post('/query', dependencies=[Depends(authorize)])
def query(body: Query):
    try:
        return query_records(str(body.householdId), body.actorId, body.question,
                             str(body.itemId) if body.itemId else None, str(body.roomId) if body.roomId else None, body.imagePath)
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        raise HTTPException(503, 'Retrieval service unavailable')


class AudioQuery(BaseModel):
    householdId: UUID
    actorId: str = Field(min_length=1, max_length=200)
    audioPath: str


@app.post('/transcribe', dependencies=[Depends(authorize)])
def transcribe_question(body: AudioQuery):
    with psycopg.connect(settings.database_url) as conn:
        if not conn.execute('SELECT 1 FROM memberships WHERE household_id=%s AND user_id=%s', (body.householdId, body.actorId)).fetchone():
            raise HTTPException(403, 'Household membership required')
    try:
        path = settings.private_path(body.audioPath)
        probe_media(path)
        chunks = transcribe(path)
        with psycopg.connect(settings.database_url) as conn:
            if not conn.execute('SELECT 1 FROM memberships WHERE household_id=%s AND user_id=%s', (body.householdId, body.actorId)).fetchone():
                raise HTTPException(403, 'Household membership was removed')
        return {'text': ' '.join(chunk.text for chunk in chunks), 'segments': [
            {'text': chunk.text, 'start': chunk.start_seconds, 'end': chunk.end_seconds} for chunk in chunks]}
    except ValueError as exc:
        raise HTTPException(422, str(exc))
