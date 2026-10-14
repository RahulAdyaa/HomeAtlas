import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { api, ApiError, audit, linkedIds, rateLimit, requireRole, scope, uuid } from '@/lib/server';
import { pool, transaction, camel } from '@/lib/db';
import { reserve, prices } from '@/lib/credits';
import { maxUploadBytes, removePrivateFile, validateFile, writeOriginal } from '@/lib/storage';
export const runtime='nodejs';
export const POST=api(async(request)=>{
 const context=await scope(request);requireRole(context,['owner','editor']);await rateLimit(`upload:${context.user.id}`,15);
 if(Number(request.headers.get('content-length')??0)>maxUploadBytes+65536)throw new ApiError(413,'This file is too large.');
 const form=await request.formData();const file=form.get('file');if(!(file instanceof File))throw new ApiError(400,'Choose a file to upload.');
 const valid=await validateFile(file);const itemId=form.get('itemId')?uuid.parse(form.get('itemId')):null;let roomId=form.get('roomId')?uuid.parse(form.get('roomId')):null;
 const existingSourceId=form.get('sourceId')?uuid.parse(form.get('sourceId')):null;
 const operationId=z.string().min(8).max(128).parse(form.get('operationId')??randomUUID());
 const sourceId=existingSourceId??randomUUID(),versionId=randomUUID();let storagePath:string|undefined;
 try{
  const result=await transaction(async(db)=>{
   const member=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2 FOR SHARE',[context.householdId,context.user.id])).rows[0];if(!member||member.role==='viewer')throw new ApiError(403,'Your role no longer allows uploads.');
   await linkedIds(db,context.householdId,itemId,roomId);
   if(itemId&&!roomId)roomId=(await db.query('SELECT room_id FROM items WHERE household_id=$1 AND id=$2',[context.householdId,itemId])).rows[0].room_id;
   let source;
   if(existingSourceId){source=(await db.query('SELECT * FROM sources WHERE id=$1 AND household_id=$2 FOR UPDATE',[sourceId,context.householdId])).rows[0];if(!source)throw new ApiError(404,'Source not found.');}
   const state=await reserve(db,context.householdId,context.user.id,operationId,`upload:${valid.sha256}:${existingSourceId??'new'}:${itemId??''}:${roomId??''}`,prices.upload);
   if(state!=='created'){
    const job=(await db.query('SELECT source_id,version_id,status FROM ingestion_jobs WHERE household_id=$1 AND operation_id=$2',[context.householdId,operationId])).rows[0];
    if(!job)throw new ApiError(409,'This operation has already been used.');return{...camel(job),replayed:true};
   }
   if(!source)await db.query('INSERT INTO sources(id,household_id,item_id,room_id,title,mime_type,created_by) VALUES($1,$2,$3,$4,$5,$6,$7)',[sourceId,context.householdId,itemId,roomId,valid.name,valid.mime,context.user.id]);
   const version=Number((await db.query('SELECT COALESCE(MAX(version),0)+1 AS next FROM source_versions WHERE source_id=$1 AND household_id=$2',[sourceId,context.householdId])).rows[0].next);
   storagePath=await writeOriginal(context.householdId,sourceId,versionId,valid);
   await db.query('INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES($1,$2,$3,$4,$5,$6,$7,$8)',[versionId,context.householdId,sourceId,version,storagePath,valid.sha256,valid.bytes.length,valid.mime]);
   await db.query("UPDATE sources SET current_version_id=$1,status='queued',mime_type=$2 WHERE id=$3 AND household_id=$4",[versionId,valid.mime,sourceId,context.householdId]);
   await db.query('INSERT INTO ingestion_jobs(household_id,source_id,version_id,actor_id,operation_id) VALUES($1,$2,$3,$4,$5)',[context.householdId,sourceId,versionId,context.user.id,operationId]);
   await audit(db,context.householdId,context.user.id,'Uploaded source',sourceId,{title:valid.name,version});return{sourceId,versionId,status:'queued',operationId,cost:prices.upload};
  });
  return Response.json(result,{status:202});
 }catch(error){if(storagePath)await removePrivateFile(storagePath);throw error;}
});
