import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { api, ApiError, audit, rateLimit, requireRole, scope, uuid } from '@/lib/server';
import { transaction } from '@/lib/db';
import { reserve, prices } from '@/lib/credits';
export const runtime='nodejs';
export const POST=api(async(request,route:{params:Promise<{id:string}>})=>{
 const context=await scope(request);requireRole(context,['owner','editor']);await rateLimit(`upload:${context.user.id}`,15);
 const id=uuid.parse((await route.params).id);const body=await request.json().catch(()=>({}));const operationId=z.string().min(8).max(128).parse(body.operationId??randomUUID());
 const result=await transaction(async(db)=>{
  const member=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2 FOR SHARE',[context.householdId,context.user.id])).rows[0];if(!member||member.role==='viewer')throw new ApiError(403,'Your role no longer allows ingestion.');
  const source=(await db.query('SELECT * FROM sources WHERE household_id=$1 AND id=$2 FOR UPDATE',[context.householdId,id])).rows[0];if(!source)throw new ApiError(404,'Source not found.');
  const existing=(await db.query('SELECT id,status FROM ingestion_jobs WHERE household_id=$1 AND operation_id=$2 AND source_id=$3',[context.householdId,operationId,id])).rows[0];if(existing)return{jobId:existing.id,status:existing.status,replayed:true};
  if(['queued','processing'].includes(source.status))throw new ApiError(409,'This source is already being processed.');
  const state=await reserve(db,context.householdId,context.user.id,operationId,`reindex:${source.current_version_id}`,prices.upload);if(state!=='created')throw new ApiError(409,'This operation ID has already been used.');
  // Keep original and previous chunks; the worker atomically replaces only this version’s index on success.
  const{rows}=await db.query('INSERT INTO ingestion_jobs(household_id,source_id,version_id,actor_id,operation_id) VALUES($1,$2,$3,$4,$5) RETURNING id',[context.householdId,id,source.current_version_id,context.user.id,operationId]);
  await db.query("UPDATE sources SET status='queued' WHERE id=$1 AND household_id=$2",[id,context.householdId]);
  await audit(db,context.householdId,context.user.id,'Queued source reprocessing',id);return{jobId:rows[0].id,status:'queued',cost:prices.upload};
 });return Response.json(result,{status:202});
});
