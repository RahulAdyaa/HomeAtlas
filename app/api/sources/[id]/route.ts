import { api, ApiError, scope, uuid } from '@/lib/server';
import { pool,camel } from '@/lib/db';
import { privateMedia } from '@/lib/media';
export const runtime='nodejs';
export const GET=api(async(request,route:{params:Promise<{id:string}>})=>{
 const context=await scope(request);const id=uuid.parse((await route.params).id);const url=new URL(request.url);const version=url.searchParams.get('version');if(version)uuid.parse(version);
 const {rows}=await pool.query('SELECT s.id,s.title,s.current_version_id,v.id AS version_id,v.storage_path,v.mime_type,v.version,v.sha256,v.size_bytes FROM sources s JOIN source_versions v ON v.source_id=s.id AND v.household_id=s.household_id AND v.id=COALESCE($3::uuid,s.current_version_id) WHERE s.id=$1 AND s.household_id=$2',[id,context.householdId,version]);
 if(!rows.length)throw new ApiError(404,'Source not found.');const source=rows[0];
 if(url.searchParams.get('metadata')==='true'){
  const versions=await pool.query('SELECT id,version,mime_type,size_bytes,sha256,created_at FROM source_versions WHERE source_id=$1 AND household_id=$2 ORDER BY version DESC',[id,context.householdId]);
  const chunks=await pool.query('SELECT id,page,bbox,start_seconds AS start,end_seconds AS end,text,modality FROM chunks WHERE household_id=$1 AND source_id=$2 AND version_id=$3 ORDER BY page NULLS LAST,start_seconds NULLS LAST,created_at LIMIT 500',[context.householdId,id,source.version_id]);
  return Response.json({id:source.id,title:source.title,versionId:source.version_id,version:source.version,versions:versions.rows.map(row=>camel(row)),chunks:chunks.rows.map(row=>camel(row))});
 }
 return privateMedia(request,source.storage_path,source.mime_type,source.title);
});
