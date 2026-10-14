import { auth } from './auth';
import { pool, type DB } from './db';
import { z } from 'zod';
import { randomUUID } from 'node:crypto';
export class ApiError extends Error {constructor(public status:number,message:string){super(message);}}
export const uuid=z.string().uuid();
export const shortText=z.string().trim().min(1).max(160);
export function sameOrigin(request:Request) {
 if(['GET','HEAD','OPTIONS'].includes(request.method)) return;
 const origin=request.headers.get('origin');
 const expected=new URL(process.env.BETTER_AUTH_URL??request.url).origin;
 if(origin!==expected) throw new ApiError(403,'This request must come from HomeAtlas.');
 if(request.headers.get('sec-fetch-site')==='cross-site') throw new ApiError(403,'Cross-site request denied.');
}
export async function session(request:Request) {
 const value=await auth.api.getSession({headers:request.headers});
 if(!value?.user || !value.user.emailVerified) throw new ApiError(401,'Sign in with a verified email to continue.');
 return value;
}
export async function scope(request:Request,householdId?:string|null) {
 const signed=await session(request);
 const chosen=householdId??new URL(request.url).searchParams.get('householdId')??request.headers.get('x-household-id');
 if(chosen) uuid.parse(chosen);
 const result=await pool.query('SELECT m.*,h.name,h.kind,h.address,h.created_at AS household_created_at FROM memberships m JOIN households h ON h.id=m.household_id WHERE m.user_id=$1 AND ($2::uuid IS NULL OR m.household_id=$2) ORDER BY m.created_at LIMIT 1',[signed.user.id,chosen??null]);
 if(!result.rows[0]) throw new ApiError(404,'Household not found.');
 return {...signed,householdId:result.rows[0].household_id as string,role:result.rows[0].role as 'owner'|'editor'|'viewer',membership:result.rows[0]};
}
export type Scope=Awaited<ReturnType<typeof scope>>;
export function requireRole(context:Scope,roles:Scope['role'][]) {
 if(!roles.includes(context.role)) throw new ApiError(403,'Your household role does not allow this action.');
}
export async function freshAuthentication(request:Request,context:Awaited<ReturnType<typeof session>>,password?:string) {
 if(password){
  try {await auth.api.verifyPassword({headers:request.headers,body:{password}});return;} catch {throw new ApiError(403,'Password verification failed.');}
 }
 if(Date.now()-new Date(context.session.createdAt).getTime()>15*60*1000) throw new ApiError(403,'For your security, sign in again or enter your password before this change.');
}
export async function linkedIds(db:DB,householdId:string,itemId?:string|null,roomId?:string|null){
 if(itemId){uuid.parse(itemId);const result=await db.query('SELECT room_id FROM items WHERE id=$1 AND household_id=$2',[itemId,householdId]);if(!result.rows.length)throw new ApiError(404,'Item not found.');if(roomId&&result.rows[0].room_id!==roomId)throw new ApiError(400,'Item does not belong to that room.');}
 if(roomId){uuid.parse(roomId);if(!(await db.query('SELECT 1 FROM rooms WHERE id=$1 AND household_id=$2',[roomId,householdId])).rows.length)throw new ApiError(404,'Room not found.');}
}
export async function audit(db:DB,householdId:string|null,actorId:string,action:string,targetId?:string,metadata:Record<string,unknown>={}){
 await db.query('INSERT INTO audit_events(household_id,actor_id,action,target_id,metadata) VALUES($1,$2,$3,$4,$5)',[householdId,actorId,action,targetId??null,JSON.stringify(metadata)]);
}
export async function rateLimit(key:string,max=30,seconds=60){
 const {rows}=await pool.query(`INSERT INTO rate_limits(key,count,expires_at) VALUES($1,1,now()+($2*interval '1 second')) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN rate_limits.expires_at<now() THEN 1 ELSE rate_limits.count+1 END,expires_at=CASE WHEN rate_limits.expires_at<now() THEN excluded.expires_at ELSE rate_limits.expires_at END RETURNING count`,[key,seconds]);
 if(rows[0].count>max)throw new ApiError(429,'Too many requests. Please wait a moment.');
}
export function api(handler:(request:Request,...args:any[])=>Promise<Response>) {
 return async(request:Request,...args:any[])=>{
  const requestId=randomUUID();
  try {sameOrigin(request);const response=await handler(request,...args);response.headers.set('X-Request-ID',requestId);response.headers.set('Cache-Control','private, no-store');return response;}
  catch(error){
   let status=500,message='Something went wrong. Please try again.';
   if(error instanceof ApiError){status=error.status;message=error.message;}
   else if(error instanceof z.ZodError){status=400;message=error.issues.map(x=>`${x.path.join('.')||'Input'}: ${x.message}`).join('; ');}
   else if(error instanceof SyntaxError){status=400;message='Invalid request body.';}
   else if(error instanceof Error&&error.message.includes('Insufficient credits')){status=402;message='There are not enough credits for this operation.';}
   else if(error instanceof Error&&error.message.includes('Operation ID conflict')){status=409;message='This operation ID has already been used.';}
   // Do not log source text, tokens, query bodies, database error details or paths.
   if(status>=500)console.error(JSON.stringify({event:'api_error',requestId,errorType:error instanceof Error?error.name:'unknown'}));
   return Response.json({error:message,requestId},{status,headers:{'X-Request-ID':requestId,'Cache-Control':'private, no-store'}});
  }
 };
}
