"""Owner-operated, no-credit PDF reindex. Run with --source-id UUID --apply.

Dry-run is the default. Originals are hash-checked, old citation rows retained,
and new chunks published transactionally only if the source version/location is unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import settings
from .ingestion import extract_pdf
from .jobs import connect, sha256_stream
from .models import models


def reindex(source:dict, apply:bool):
    path=settings.private_path(source['storage_path'])
    with path.open('rb') as original:
        if sha256_stream(original)!=source['sha256']:
            raise ValueError('Original hash mismatch; source was not changed')
    if not apply:
        with TemporaryDirectory(prefix='homeatlas-clean-pdf-preview-') as temporary:
            return len(extract_pdf(path,Path(temporary)))
    artifacts=settings.storage/'derived'/str(source['household_id'])/str(source['current_version_id'])/('clean-pdf-'+str(uuid.uuid4()))
    artifacts.mkdir(parents=True,exist_ok=True)
    chunks=extract_pdf(path,artifacts)
    for chunk in chunks:
        chunk.metadata['content_text']=chunk.text
        chunk.text=f"Location: {source['location_path']}\n\n{chunk.text}"
    vectors=models.embed_text([chunk.text for chunk in chunks])
    images={}
    for chunk in chunks:
        if chunk.image_path and chunk.image_path not in images:
            images[chunk.image_path]=models.embed_image_space(image=Path(chunk.image_path))
    with connect(settings) as conn:
        current=conn.execute('''SELECT s.current_version_id,s.location_id,s.location_path,s.status,v.sha256
            FROM sources s JOIN source_versions v ON v.id=s.current_version_id AND v.household_id=s.household_id
            WHERE s.id=%s AND s.household_id=%s FOR UPDATE OF s''',(source['id'],source['household_id'])).fetchone()
        if (not current or current['current_version_id']!=source['current_version_id'] or
                current['location_id']!=source['location_id'] or current['location_path']!=source['location_path'] or
                current['sha256']!=source['sha256'] or current['status']!='ready'):
            raise RuntimeError('Source changed during extraction; retry from current version')
        conn.execute("UPDATE chunks SET metadata=jsonb_set(metadata,'{active}','false'::jsonb) WHERE household_id=%s AND version_id=%s",(source['household_id'],source['current_version_id']))
        for index,chunk in enumerate(chunks):
            fingerprint=json.dumps([index,chunk.text,chunk.page,chunk.bbox,chunk.start_seconds,chunk.end_seconds,chunk.modality])
            chunk_id=uuid.uuid5(uuid.UUID(str(source['current_version_id'])),fingerprint)
            vector=images.get(chunk.image_path)
            metadata=dict(chunk.metadata,source_sha256=source['sha256'],source_version=source['version'],
                          location_id=str(source['location_id']),location_path=source['location_path'],
                          permissions='household-members',extractor_version='homeatlas-3-clean-pdf',active=True)
            conn.execute('''INSERT INTO chunks(id,household_id,source_id,version_id,item_id,room_id,text,page,bbox,
                start_seconds,end_seconds,modality,embedding,embedding_model,model_revision,image_path,metadata,image_embedding,image_embedding_model)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                embedding=EXCLUDED.embedding,embedding_model=EXCLUDED.embedding_model,model_revision=EXCLUDED.model_revision,
                image_embedding=EXCLUDED.image_embedding,image_embedding_model=EXCLUDED.image_embedding_model,
                metadata=EXCLUDED.metadata''',
                (chunk_id,source['household_id'],source['id'],source['current_version_id'],source['item_id'],source['room_id'],
                 chunk.text,chunk.page,Jsonb(chunk.bbox) if chunk.bbox else None,chunk.start_seconds,chunk.end_seconds,
                 chunk.modality,vectors[index] if vectors else None,models.text_identity if vectors else None,
                 models.cfg.text_revision if vectors else None,chunk.image_path,Jsonb(metadata),vector,
                 models.image_identity if vector else None))
        # Chunk triggers also advance the version; this explicit update covers
        # an unchanged/empty extraction and makes maintenance invalidation clear.
        conn.execute('UPDATE households SET data_version=data_version+1 WHERE id=%s',(source['household_id'],))
    return len(chunks)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-id',required=True,help='Exact source UUID in the local database')
    parser.add_argument('--title',help='Optional expected title guard')
    parser.add_argument('--apply',action='store_true',help='Atomically replace the active index without charging credits')
    args=parser.parse_args()
    source_id=uuid.UUID(args.source_id)
    with connect(settings) as conn:
        rows=conn.execute('''SELECT s.*,v.storage_path,v.sha256,v.version FROM sources s
            JOIN source_versions v ON v.id=s.current_version_id AND v.household_id=s.household_id
            WHERE s.id=%s AND s.status='ready' AND v.mime_type='application/pdf' ''',(source_id,)).fetchall()
    if len(rows)!=1 or (args.title and rows[0]['title']!=args.title):
        raise SystemExit('Source ID did not identify the expected ready PDF')
    print(json.dumps({'title':rows[0]['title'],'chunks':reindex(rows[0],args.apply),'applied':args.apply}))


if __name__=='__main__':main()
