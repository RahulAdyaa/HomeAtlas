import { api, ApiError, scope, uuid } from '@/lib/server';
import { pool,camel } from '@/lib/db';
import { privateMedia } from '@/lib/media';
export const runtime='nodejs';
export const GET=api(async(request,route:{params:Promise<{id:string}>})=>{
 const context=await scope(request);const id=uuid.parse((await route.params).id);
 const{rows}=await pool.query('SELECT c.id,c.source_id,c.version_id,c.page,c.bbox,c.start_seconds AS start,c.end_seconds AS end,c.text,c.modality,c.image_path,s.title,v.mime_type FROM chunks c JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id JOIN source_versions v ON v.id=c.version_id AND v.source_id=c.source_id AND v.household_id=c.household_id WHERE c.id=$1 AND c.household_id=$2',[id,context.householdId]);
 if(!rows.length)throw new ApiError(404,'Citation not found.');const citation=rows[0];
 if(new URL(request.url).searchParams.get('preview')==='true'&&citation.image_path)return privateMedia(request,citation.image_path,'image/png',`${citation.title} preview`);
 delete citation.image_path;return Response.json(camel(citation));
});
