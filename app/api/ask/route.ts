import { createHash,randomUUID } from 'node:crypto';
import { z } from 'zod';
import { api, ApiError, audit, linkedIds, rateLimit, scope, uuid } from '@/lib/server';
import { pool,transaction,camel } from '@/lib/db';
import { prices,reserve,settle } from '@/lib/credits';
import { maxUploadBytes,removePrivateFile,validateFile,writeQueryMedia } from '@/lib/storage';
import {lookupSavedRecord} from '@/lib/item-facts';
import {locationLink,locationSentence} from '@/lib/locations';
import { callWorker } from '@/lib/worker';
export const runtime='nodejs';
export const maxDuration=300;
const replySchema=z.object({recordFacts:z.array(z.object({kind:z.literal('item'),id:uuid,name:z.string(),field:z.string(),label:z.string(),value:z.string().nullable(),locationPath:z.string()})).max(5).default([]),locationMatches:z.array(z.object({kind:z.enum(['item','source']),id:uuid,name:z.string(),locationId:uuid,locationPath:z.string(),locationUrl:z.string(),locationDescription:z.string(),photoSourceId:uuid.nullish()})).max(60).default([]),answer:z.string().max(30000),confidence:z.string().max(80),mode:z.string().max(80),citations:z.array(z.object({id:uuid,sourceId:uuid,versionId:uuid,text:z.string().min(8).max(12000)}).passthrough()).max(30),suggestion:z.string().max(3000).optional(),diagnostics:z.record(z.string(),z.unknown()).optional()});
export const POST=api(async(request)=>{
 const context=await scope(request);await rateLimit(`ask:${context.user.id}`,12);
 if(Number(request.headers.get('content-length')??0)>maxUploadBytes+65536)throw new ApiError(413,'This question attachment is too large.');
 const multipart=request.headers.get('content-type')?.includes('multipart/form-data');
 const form=multipart?await request.formData():null;const json=form?null:await request.json();const value=(key:string)=>form?form.get(key):json?.[key];
 const image=value('image'),audio=value('audio');if(image instanceof File&&audio instanceof File)throw new ApiError(400,'Attach a photo or a voice recording, one at a time.');
 let question=z.string().trim().max(3000).parse(value('question')??'');
 if(!question&&!(audio instanceof File)&&!(image instanceof File))throw new ApiError(400,'Enter a question or record a voice note.');
 const itemId=value('itemId')?uuid.parse(value('itemId')):null,roomId=value('roomId')?uuid.parse(value('roomId')):null;
 await linkedIds(pool,context.householdId,itemId,roomId);
 const bypassCache=value('bypassCache')===true||value('bypassCache')==='true';
 const operationId=z.string().min(8).max(128).parse(value('operationId')??randomUUID());
 const media=image instanceof File?await validateFile(image,'image'):audio instanceof File?await validateFile(audio,'audio'):null;
 if(!question&&image instanceof File)question='What evidence in my household records relates to this photo?';
 const cost=image instanceof File?prices.imageQuestion:audio instanceof File?prices.voiceQuestion:prices.question;
 const fingerprint=createHash('sha256').update(JSON.stringify({question,itemId,roomId,media:media?.sha256,type:image instanceof File?'image':audio instanceof File?'audio':'text'})).digest('hex');
 let mediaPath:string|undefined,held=false;
 try{
  const prior=await transaction(async(db)=>{
   const state=await reserve(db,context.householdId,context.user.id,operationId,`question:${fingerprint}`,cost);
   if(state==='created'){held=true;return null;}
   const reservation=(await db.query('SELECT result,status FROM credit_reservations WHERE household_id=$1 AND operation_id=$2',[context.householdId,operationId])).rows[0];
   if(reservation.status==='charged'&&reservation.result)return reservation.result;
   if(reservation.status==='refunded')throw new ApiError(409,'This attempt was refunded. Start a new question to try again.');
   throw new ApiError(409,'This question is already processing. Please wait before trying again.');
  });
  if(prior){if(context.role!=='owner')delete prior.diagnostics;return Response.json({...prior,replayed:true});}
  if(media)mediaPath=await writeQueryMedia(context.householdId,media);
  let transcription:string|undefined;
  if(audio instanceof File){const transcript=await callWorker('/transcribe',{householdId:context.householdId,actorId:context.user.id,audioPath:mediaPath},request.signal);transcription=z.string().trim().min(1).max(3000).parse(transcript.text);question=question?`${question}\nVoice note: ${transcription}`.slice(0,3000):transcription;}
  const retrievalStarted=Date.now();
  const cacheBody={householdId:context.householdId,actorId:context.user.id,question,scopeKey:JSON.stringify({itemId,roomId}),bypass:bypassCache};
  // Media questions are deliberately not reused by text-only cache keys.
  let cached: {hit:boolean;dataVersion?:string;answer?:unknown;kind?:string}={hit:false};
  if(!media)try{cached=await callWorker('/cache/lookup',cacheBody,request.signal) as typeof cached;}catch{/* Cache failure must not block retrieval. */}
  const recorded=!cached.hit&&!(image instanceof File)?await lookupSavedRecord(pool,context.householdId,question,itemId,roomId):null;
  const raw=cached.hit?cached.answer:recorded??await callWorker('/query',{householdId:context.householdId,actorId:context.user.id,question,itemId,roomId,imagePath:image instanceof File?mediaPath:undefined},request.signal);
  const reply=replySchema.parse(raw);
  const answer=await transaction(async(db)=>{
   const member=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2 FOR SHARE',[context.householdId,context.user.id])).rows[0];if(!member)throw new ApiError(403,'Your household membership was removed.');
   const version=(await db.query('SELECT data_version FROM households WHERE id=$1 FOR SHARE',[context.householdId])).rows[0].data_version;
   if(cached.hit&&String(version)!==cached.dataVersion)throw new ApiError(409,'Your records changed while checking. Please ask again.');
   if(recorded){const current=await lookupSavedRecord(db,context.householdId,question,itemId,roomId);Object.assign(reply,current??{answer:'This saved record changed while checking. Please ask again.',confidence:'insufficient',mode:'abstention',locationMatches:[],recordFacts:[]});}
   if(member.role!=='owner')delete reply.diagnostics;
   const citations=[];
   for(const citation of reply.citations){
    const{rows}=await db.query('SELECT c.id,c.source_id,c.version_id,s.title,s.location_id,s.location_path,c.page,c.bbox,c.text,c.start_seconds AS start,c.end_seconds AS end,c.modality,c.metadata FROM chunks c JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id WHERE c.household_id=$1 AND c.id=$2 AND c.source_id=$3 AND c.version_id=$4 AND s.current_version_id=c.version_id',[context.householdId,citation.id,citation.sourceId,citation.versionId]);
    if(!rows.length||!rows[0].text.includes(citation.text))throw new ApiError(502,'The answer included evidence that could not be verified. Please try again.');
    citations.push({...camel(rows[0]),text:citation.text,locationUrl:locationLink(context.householdId,rows[0].location_id),locationDescription:locationSentence(rows[0].title,rows[0].location_path),number:citations.length+1});
   }
   const conversationId=randomUUID();
   const result={...reply,citations,cache:{hit:cached.hit,kind:cached.kind??'miss'},operationId,cost,conversationId,...(transcription?{transcription}:{})};
   await db.query('INSERT INTO conversations(id,household_id,user_id,title) VALUES($1,$2,$3,$4)',[conversationId,context.householdId,context.user.id,question.slice(0,160)]);
   await db.query("INSERT INTO messages(household_id,conversation_id,role,content) VALUES($1,$2,'user',$3)",[context.householdId,conversationId,question]);
   await db.query("INSERT INTO messages(household_id,conversation_id,role,content,citations,metadata) VALUES($1,$2,'assistant',$3,$4,$5)",[context.householdId,conversationId,result.answer,JSON.stringify(citations),JSON.stringify({confidence:result.confidence,mode:result.mode,locationMatches:result.locationMatches,recordFacts:result.recordFacts})]);
   if(!await settle(db,context.householdId,operationId,true))throw new ApiError(409,'This question reservation expired or was refunded. Start a new question to try again.');
   await db.query('UPDATE credit_reservations SET result=$3 WHERE household_id=$1 AND operation_id=$2',[context.householdId,operationId,JSON.stringify(result)]);
   await audit(db,context.householdId,context.user.id,'Asked household records',conversationId,{mode:result.mode,citations:citations.length});return result;
  });
  held=false;
  if(!media&&!cached.hit&&!bypassCache&&cached.dataVersion)try{await callWorker('/cache/store',{...cacheBody,dataVersion:cached.dataVersion,answer,latencyMs:Date.now()-retrievalStarted},request.signal);}catch{/* Cache writes are best effort after the charged result is committed. */}
  return Response.json(answer);
 }catch(error){
  if(held)await transaction(async(db)=>{if((await db.query('SELECT 1 FROM credit_reservations WHERE household_id=$1 AND operation_id=$2',[context.householdId,operationId])).rows.length)await settle(db,context.householdId,operationId,false);});throw error;
 }finally{if(mediaPath)await removePrivateFile(mediaPath);}
});
