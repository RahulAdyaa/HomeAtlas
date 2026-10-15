"""Queue an OCR upgrade using already-settled jobs, without new credit reservations.
Usage: worker/.venv/bin/python scripts/reindex-image-sources.py HOUSEHOLD_UUID
Originals and old citation rows are retained by the existing atomic worker publisher.
"""
import sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import psycopg
from psycopg.rows import dict_row
from worker.config import settings
hid=str(uuid.UUID(sys.argv[1]));count=0
with psycopg.connect(settings.database_url,row_factory=dict_row) as conn:
 rows=conn.execute('''SELECT s.id,j.id job_id,j.actor_id FROM sources s
  JOIN LATERAL(SELECT j.* FROM ingestion_jobs j JOIN credit_reservations r ON r.household_id=j.household_id AND r.operation_id=j.operation_id
    WHERE j.household_id=s.household_id AND j.source_id=s.id AND j.version_id=s.current_version_id AND j.status='ready' AND r.status='charged'
    ORDER BY j.created_at DESC LIMIT 1) j ON true
  JOIN memberships m ON m.household_id=s.household_id AND m.user_id=j.actor_id AND m.role IN ('owner','editor')
  WHERE s.household_id=%s AND s.status='ready' AND (s.mime_type LIKE 'image/%%' OR s.mime_type='application/pdf')
  AND EXISTS(SELECT 1 FROM chunks c WHERE c.source_id=s.id AND c.version_id=s.current_version_id AND coalesce(c.metadata->>'active','true')='true'
    AND c.image_path IS NOT NULL AND c.metadata->>'extractor_version' IS DISTINCT FROM 'homeatlas-2-image-evidence')
  FOR UPDATE OF s''',(hid,)).fetchall()
 for row in rows:
  conn.execute("UPDATE ingestion_jobs SET status='queued',attempts=0,error=NULL,claim_token=NULL WHERE id=%s",(row['job_id'],))
  conn.execute("UPDATE sources SET status='queued' WHERE id=%s",(row['id'],))
  conn.execute("INSERT INTO audit_events(household_id,actor_id,action,target_id,metadata) VALUES(%s,%s,'source.image-index-upgrade',%s,'{\"additionalCharge\":false}'::jsonb)",(hid,row['actor_id'],str(row['id'])))
  count+=1
print({'queuedForImageIndexUpgrade':count,'newCreditReservations':0})
