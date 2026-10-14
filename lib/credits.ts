import { type DB } from './db';
function price(key:string,defaultValue:number){const n=Number(process.env[key]??defaultValue);if(!Number.isInteger(n)||n<1)throw new Error(`Invalid credit setting ${key}`);return n;}
export const prices={upload:price('CREDIT_COST_UPLOAD',5),question:price('CREDIT_COST_QUESTION',1),imageQuestion:price('CREDIT_COST_IMAGE_QUESTION',3),voiceQuestion:price('CREDIT_COST_VOICE_QUESTION',3)};
export const monthlyAllowance=price('MONTHLY_CREDITS',100);
export async function ensureMonthlyGrant(db:DB,householdId:string,actorId?:string){
 // HTTP questions time out after at most five minutes. Recover reservations left by a killed
 // Node process after a longer ten-minute grace period, preserving an explicit refund event.
 const expired=await db.query("SELECT operation_id FROM credit_reservations WHERE household_id=$1 AND status='reserved' AND kind LIKE 'question:%' AND created_at<now()-interval '10 minutes'",[householdId]);
 for(const row of expired.rows)await db.query('SELECT atlas_settle_credit($1,$2,false)',[householdId,row.operation_id]);
 await db.query("SELECT atlas_grant_credit($1,'monthly:'||to_char(now() AT TIME ZONE 'UTC','YYYY-MM'),$2,$3)",[householdId,monthlyAllowance,actorId??null]);
}
export async function reserve(db:DB,householdId:string,actorId:string,operationId:string,kind:string,cost:number){
 await ensureMonthlyGrant(db,householdId,actorId);
 return (await db.query('SELECT atlas_reserve_credit($1,$2,$3,$4,$5) AS status',[householdId,operationId,kind,cost,actorId])).rows[0].status as string;
}
export async function settle(db:DB,householdId:string,operationId:string,success:boolean){
 return (await db.query('SELECT atlas_settle_credit($1,$2,$3) AS changed',[householdId,operationId,success])).rows[0].changed as boolean;
}
