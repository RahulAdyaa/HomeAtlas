import { api,scope,requireRole } from '@/lib/server';
import { pool,camel } from '@/lib/db';
import { workerHealth } from '@/lib/worker';
export const runtime='nodejs';
export const GET=api(async(request)=>{
 const context=await scope(request);requireRole(context,['owner']);
 const [jobs,audit,usage,permissions,worker]=await Promise.all([
  pool.query('SELECT j.id,j.source_id,s.title,j.version_id,j.status,j.attempts,j.error,j.created_at,j.started_at,j.completed_at FROM ingestion_jobs j JOIN sources s ON s.id=j.source_id AND s.household_id=j.household_id WHERE j.household_id=$1 ORDER BY j.created_at DESC LIMIT 100',[context.householdId]),
  pool.query('SELECT * FROM audit_events WHERE household_id=$1 ORDER BY created_at DESC LIMIT 100',[context.householdId]),
  pool.query('SELECT kind,count(*)::int AS entries,sum(amount)::int AS credits FROM credit_ledger WHERE household_id=$1 GROUP BY kind',[context.householdId]),
  pool.query('SELECT role,count(*)::int AS members FROM memberships WHERE household_id=$1 GROUP BY role',[context.householdId]),workerHealth()]);
 return Response.json({jobs:jobs.rows.map(row=>camel(row)),audit:audit.rows.map(row=>camel(row)),usage:usage.rows,permissions:permissions.rows,worker});
});
