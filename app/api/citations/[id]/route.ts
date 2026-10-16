import { api, ApiError, scope, uuid } from '@/lib/server';
import { pool,camel } from '@/lib/db';
import { privateMedia } from '@/lib/media';
import { authorizedPath } from '@/lib/storage';
import sharp from 'sharp';
export const runtime='nodejs';
export const GET=api(async(request,route:{params:Promise<{id:string}>})=>{
 const context=await scope(request);const id=uuid.parse((await route.params).id);
 const{rows}=await pool.query('SELECT c.id,c.source_id,c.version_id,c.page,c.bbox,c.start_seconds AS start,c.end_seconds AS end,c.text,c.modality,c.image_path,c.metadata,s.title,v.mime_type FROM chunks c JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id JOIN source_versions v ON v.id=c.version_id AND v.source_id=c.source_id AND v.household_id=c.household_id WHERE c.id=$1 AND c.household_id=$2',[id,context.householdId]);
 if(!rows.length)throw new ApiError(404,'Citation not found.');const citation=rows[0];
 if(new URL(request.url).searchParams.get('preview')==='equation'&&citation.image_path&&citation.metadata?.equation_candidate&&Array.isArray(citation.bbox)){
  const file=await authorizedPath(citation.image_path);const source=sharp(file.path,{limitInputPixels:40_000_000});const dimensions=await source.metadata();
  const width=Number(citation.metadata.width),height=Number(citation.metadata.height),box=citation.bbox.map(Number);
  if(width>0&&height>0&&dimensions.width&&dimensions.height&&box.length===4&&box.every(Number.isFinite)){
   const sx=dimensions.width/width,sy=dimensions.height/height,pad=24;
   const left=Math.max(0,Math.floor(box[0]*sx)-pad),top=Math.max(0,Math.floor(box[1]*sy)-pad);
   const right=Math.min(dimensions.width,Math.ceil(box[2]*sx)+pad),bottom=Math.min(dimensions.height,Math.ceil(box[3]*sy)+pad);
   if(right>left&&bottom>top&&right-left<=4000&&bottom-top<=4000){
    const body=await source.extract({left,top,width:right-left,height:bottom-top}).png().toBuffer();
    return new Response(new Uint8Array(body),{headers:{'Content-Type':'image/png','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'"}});
   }
  }
 }
 if(new URL(request.url).searchParams.get('preview')==='true'&&citation.image_path)return privateMedia(request,citation.image_path,'image/png',`${citation.title} preview`);
 delete citation.image_path;return Response.json(camel(citation));
});
