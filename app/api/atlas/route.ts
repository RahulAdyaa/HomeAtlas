import { z } from 'zod';
import { createHash, randomBytes } from 'node:crypto';
import { api, ApiError, audit, freshAuthentication, linkedIds, rateLimit, requireRole, scope, session, shortText, uuid } from '@/lib/server';
import { pool, transaction, camel } from '@/lib/db';
import { ensureMonthlyGrant, monthlyAllowance, prices } from '@/lib/credits';
import { sendEmail } from '@/lib/email';
import { deletePrivateHousehold } from '@/lib/storage';
export const runtime='nodejs';
const date=z.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine(value=>!Number.isNaN(Date.parse(value))&&new Date(value).toISOString().slice(0,10)===value,'Invalid date');
const optionalId=uuid.nullish();
const optionalDate=date.nullish();
const itemFields={name:shortText,roomId:optionalId,category:z.string().max(80).default('appliance'),make:z.string().max(160).default(''),model:z.string().max(160).default(''),serialNumber:z.string().max(160).default(''),purchaseDate:optionalDate,warrantyDate:optionalDate,notes:z.string().max(12000).default('')};
const actions=z.discriminatedUnion('action',[
 z.object({action:z.literal('createHousehold'),name:shortText,kind:z.enum(['home','house','apartment']).default('apartment'),address:z.string().max(500).default(''),starterRooms:z.boolean().default(true)}),
 z.object({action:z.literal('addRoom'),name:shortText,kind:z.string().max(40).default('living'),color:z.string().regex(/^#[0-9a-fA-F]{6}$/).default('#d4bfa9'),position:z.record(z.string(),z.number()).optional()}),
 z.object({action:z.literal('addItem'),...itemFields}),
 z.object({action:z.literal('updateItem'),id:uuid,...itemFields}),
 z.object({action:z.literal('addTask'),title:shortText,dueDate:date,itemId:optionalId,roomId:optionalId,recurrenceDays:z.number().int().min(1).max(3650).nullish()}),
 z.object({action:z.literal('completeTask'),id:uuid}),
 z.object({action:z.literal('invite'),email:z.email().max(254),role:z.enum(['editor','viewer']),password:z.string().optional()}),
 z.object({action:z.literal('acceptInvite'),token:z.string().min(32).max(128)}),
 z.object({action:z.literal('updateMember'),userId:z.string().min(1).max(128),role:z.enum(['owner','editor','viewer']),password:z.string().optional()}),
 z.object({action:z.literal('removeMember'),userId:z.string().min(1).max(128),password:z.string().optional()}),
 z.object({action:z.literal('bookmark'),title:shortText,question:z.string().max(4000).default(''),answer:z.string().max(16000).default(''),citations:z.array(z.object({id:uuid,sourceId:uuid,versionId:uuid}).passthrough()).max(30).default([]),itemId:optionalId}),
 z.object({action:z.literal('deleteHousehold'),confirmName:shortText,password:z.string().optional()}),
]);
export const GET=api(async(request)=>{
 const signed=await session(request);
 const membershipRows=await pool.query('SELECT m.household_id,m.role,h.name FROM memberships m JOIN households h ON h.id=m.household_id WHERE m.user_id=$1 ORDER BY m.created_at',[signed.user.id]);
 if(!membershipRows.rows.length)return Response.json({user:signed.user,household:null,membership:null,households:[],rooms:[],items:[],sources:[],tasks:[],activity:[],credits:null,members:[],bookmarks:[],history:[]});
 const context=await scope(request);const hid=context.householdId;
 await ensureMonthlyGrant(pool,hid,signed.user.id);
 const results=await Promise.all([
  pool.query('SELECT * FROM rooms WHERE household_id=$1 ORDER BY created_at',[hid]),
  pool.query('SELECT * FROM items WHERE household_id=$1 ORDER BY created_at',[hid]),
  pool.query(`SELECT s.*,v.version,v.size_bytes,j.error,j.attempts FROM sources s LEFT JOIN source_versions v ON v.id=s.current_version_id AND v.household_id=s.household_id LEFT JOIN LATERAL (SELECT error,attempts FROM ingestion_jobs WHERE source_id=s.id AND version_id=s.current_version_id ORDER BY created_at DESC LIMIT 1) j ON true WHERE s.household_id=$1 ORDER BY s.created_at DESC`,[hid]),
  pool.query('SELECT * FROM tasks WHERE household_id=$1 ORDER BY completed_at NULLS FIRST,due_date',[hid]),
  pool.query('SELECT a.id,a.action,a.target_id,a.created_at,u.name AS actor_name,a.metadata FROM audit_events a LEFT JOIN "user" u ON u.id=a.actor_id WHERE a.household_id=$1 ORDER BY a.created_at DESC LIMIT 60',[hid]),
  pool.query('SELECT * FROM credit_accounts WHERE household_id=$1',[hid]),
  pool.query('SELECT id,operation_id,kind,amount,available_delta,reserved_delta,description,actor_id,created_at FROM credit_ledger WHERE household_id=$1 ORDER BY created_at DESC LIMIT 100',[hid]),
  pool.query(`SELECT m.user_id,m.role,m.created_at,u.name,${context.role==='owner'?'u.email':'NULL::text AS email'} FROM memberships m JOIN "user" u ON u.id=m.user_id WHERE m.household_id=$1 ORDER BY m.created_at`,[hid]),
  pool.query('SELECT * FROM bookmarks WHERE household_id=$1 AND user_id=$2 ORDER BY created_at DESC',[hid,signed.user.id]),
  pool.query('SELECT * FROM maintenance_events WHERE household_id=$1 ORDER BY created_at DESC LIMIT 100',[hid]),
  pool.query('SELECT * FROM locations WHERE household_id=$1 ORDER BY created_at,id',[hid]),
 ]);
 const [rooms,items,sources,tasks,activity,account,ledger,members,bookmarks,history,locations]=results.map(x=>x.rows.map(row=>camel(row)));
 const acc=account[0] as {available:number,reserved:number};
 return Response.json({user:signed.user,household:{id:hid,name:context.membership.name,kind:context.membership.kind,address:context.membership.address,createdAt:context.membership.household_created_at},membership:{role:context.role,userId:signed.user.id,householdId:hid},households:membershipRows.rows.map(row=>camel(row)),rooms,items,sources,tasks,activity,credits:{...acc,balance:acc.available+acc.reserved,monthlyAllowance,prices,ledger},members,bookmarks,history,locations});
});
export const POST=api(async(request)=>{
 const raw=await request.json();const input=actions.parse(raw);const signed=await session(request);
 await rateLimit(`atlas:${signed.user.id}`,60);
 if(input.action==='createHousehold'){
  const household=await transaction(async(db)=>{
   const {rows}=await db.query('INSERT INTO households(name,kind,address,created_by) VALUES($1,$2,$3,$4) RETURNING *',[input.name,input.kind,input.address,signed.user.id]);const home=rows[0];
   await db.query("INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,'owner')",[home.id,signed.user.id]);
   await ensureMonthlyGrant(db,home.id,signed.user.id);
   if(input.starterRooms)for(const [name,kind,color] of [['Living room','living','#c6b391'],['Kitchen','kitchen','#b4bdac'],['Bedroom','bedroom','#c5b2bb'],['Bathroom','bathroom','#a7bec2'],['Laundry','laundry','#c7c5b0'],['Study','study','#b9b2c5']])await db.query('INSERT INTO rooms(household_id,name,kind,color) VALUES($1,$2,$3,$4)',[home.id,name,kind,color]);
   await audit(db,home.id,signed.user.id,'Created household',home.id);return camel(home);
  });return Response.json({household},{status:201});
 }
 if(input.action==='acceptInvite'){
  const householdId=await transaction(async(db)=>{
   const {rows}=await db.query('SELECT * FROM invitations WHERE token_hash=$1 AND used_at IS NULL AND expires_at>now() FOR UPDATE',[createHash('sha256').update(input.token).digest('hex')]);const invite=rows[0];
   if(!invite||invite.email.toLowerCase()!==signed.user.email.toLowerCase())throw new ApiError(404,'This invitation is invalid, expired, or belongs to another email address.');
   await db.query('INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,$3) ON CONFLICT DO NOTHING',[invite.household_id,signed.user.id,invite.role]);
   await db.query('UPDATE invitations SET used_at=now() WHERE id=$1',[invite.id]);
   await audit(db,invite.household_id,signed.user.id,'Joined household',signed.user.id);
   return invite.household_id;
  });return Response.json({ok:true,householdId});
 }
 const context=await scope(request,raw.householdId);const hid=context.householdId;
 const ownerActions=['invite','updateMember','removeMember','deleteHousehold'];
 requireRole(context,input.action==='bookmark'?['owner','editor','viewer']:ownerActions.includes(input.action)?['owner']:['owner','editor']);
 if(ownerActions.includes(input.action))await freshAuthentication(request,signed,'password' in input?input.password:undefined);
 let email: {to:string,subject:string,text:string}|undefined;
 const result=await transaction(async(db)=>{
  if(ownerActions.includes(input.action))await db.query('SELECT id FROM households WHERE id=$1 FOR UPDATE',[hid]);
  const member=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2 FOR SHARE',[hid,signed.user.id])).rows[0];
  if(!member||member.role!==context.role)throw new ApiError(403,'Your household permissions changed. Refresh and try again.');
  switch(input.action){
   case 'addRoom':{const {rows}=await db.query('INSERT INTO rooms(household_id,name,kind,color,position) VALUES($1,$2,$3,$4,$5) RETURNING *',[hid,input.name,input.kind,input.color,JSON.stringify(input.position??{})]);await audit(db,hid,signed.user.id,'Added room',rows[0].id,{name:input.name});return{room:camel(rows[0])};}
   case 'addItem':case 'updateItem':{
    await linkedIds(db,hid,null,input.roomId);
    const values=[hid,input.name,input.roomId??null,input.category,input.make,input.model,input.serialNumber,input.purchaseDate??null,input.warrantyDate??null,input.notes];
    const result=input.action==='addItem'?await db.query('INSERT INTO items(household_id,name,room_id,category,make,model,serial_number,purchase_date,warranty_date,notes) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING *',values):await db.query('UPDATE items SET name=$2,room_id=$3,category=$4,make=$5,model=$6,serial_number=$7,purchase_date=$8,warranty_date=$9,notes=$10,updated_at=now() WHERE household_id=$1 AND id=$11 RETURNING *',[...values,input.id]);
    if(!result.rows.length)throw new ApiError(404,'Item not found.');await audit(db,hid,signed.user.id,input.action==='addItem'?'Added item':'Updated item',result.rows[0].id,{name:input.name});return{item:camel(result.rows[0])};
   }
   case 'addTask':{await linkedIds(db,hid,input.itemId,input.roomId);const{rows}=await db.query('INSERT INTO tasks(household_id,title,due_date,item_id,room_id,recurrence_days,created_by) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING *',[hid,input.title,input.dueDate,input.itemId??null,input.roomId??null,input.recurrenceDays??null,signed.user.id]);await audit(db,hid,signed.user.id,'Added maintenance reminder',rows[0].id,{title:input.title});return{task:camel(rows[0])};}
   case 'completeTask':{
    const{rows}=await db.query('UPDATE tasks SET completed_at=now() WHERE household_id=$1 AND id=$2 AND completed_at IS NULL RETURNING *',[hid,input.id]);
    if(!rows.length)throw new ApiError(404,'Task not found or already complete.');const task=rows[0];
    await db.query('INSERT INTO maintenance_events(household_id,item_id,task_id,user_id,description) VALUES($1,$2,$3,$4,$5)',[hid,task.item_id,task.id,signed.user.id,task.title]);
    if(task.recurrence_days)await db.query("INSERT INTO tasks(household_id,title,due_date,item_id,room_id,recurrence_days,created_by) VALUES($1,$2,GREATEST($3::date,CURRENT_DATE)+$4::int,$5,$6,$4,$7)",[hid,task.title,task.due_date,task.recurrence_days,task.item_id,task.room_id,signed.user.id]);
    await audit(db,hid,signed.user.id,'Completed maintenance',task.id,{title:task.title});return{ok:true};
   }
   case 'invite':{const token=randomBytes(32).toString('hex');const url=`${process.env.BETTER_AUTH_URL??'http://localhost:3000'}/?invite=${token}`;
    await db.query("INSERT INTO invitations(household_id,email,role,token_hash,expires_at,created_by) VALUES($1,$2,$3,$4,now()+interval '7 days',$5)",[hid,input.email.toLowerCase(),input.role,createHash('sha256').update(token).digest('hex'),signed.user.id]);
    email={to:input.email,subject:`Join ${context.membership.name} on HomeAtlas`,text:`${signed.user.name} invited you to join their household as ${input.role}. Sign in with ${input.email} and open this one-use link within 7 days: ${url}`};
    await audit(db,hid,signed.user.id,'Invited member',undefined,{role:input.role});return{ok:true,inviteUrl:url};
   }
   case 'updateMember':case 'removeMember':{
    const target=(await db.query('SELECT * FROM memberships WHERE household_id=$1 AND user_id=$2 FOR UPDATE',[hid,input.userId])).rows[0];if(!target)throw new ApiError(404,'Member not found.');
    if(target.role==='owner'&&(input.action==='removeMember'||input.role!=='owner')){const owners=await db.query("SELECT user_id FROM memberships WHERE household_id=$1 AND role='owner'",[hid]);if(owners.rows.length<=1)throw new ApiError(409,'A household must keep at least one owner.');}
    if(input.action==='updateMember')await db.query('UPDATE memberships SET role=$3 WHERE household_id=$1 AND user_id=$2',[hid,input.userId,input.role]);else await db.query('DELETE FROM memberships WHERE household_id=$1 AND user_id=$2',[hid,input.userId]);
    await audit(db,hid,signed.user.id,input.action==='updateMember'?'Updated member role':'Removed member',input.userId,input.action==='updateMember'?{role:input.role}:{});return{ok:true};
   }
   case 'bookmark':{
    if(input.itemId&&context.role==='viewer')throw new ApiError(403,'Only owners and editors can save answers to shared item history.');
    await linkedIds(db,hid,input.itemId);
    // Persist canonical citation fields from authorized immutable chunks, never browser-supplied content or paths.
    const citations=[];
    for(const citation of input.citations){const{rows}=await db.query('SELECT c.id,c.source_id,c.version_id,s.title,c.page,c.bbox,c.text,c.start_seconds AS start,c.end_seconds AS end FROM chunks c JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id WHERE c.household_id=$1 AND c.id=$2 AND c.source_id=$3 AND c.version_id=$4',[hid,citation.id,citation.sourceId,citation.versionId]);if(!rows.length)throw new ApiError(404,'Citation not found.');citations.push(camel(rows[0]));}
    const{rows}=await db.query('INSERT INTO bookmarks(household_id,user_id,title,question,answer,citations,item_id) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING *',[hid,signed.user.id,input.title,input.question,input.answer,JSON.stringify(citations),input.itemId??null]);
    if(input.itemId)await db.query('INSERT INTO maintenance_events(household_id,item_id,user_id,description) VALUES($1,$2,$3,$4)',[hid,input.itemId,signed.user.id,`${input.title}\n${input.answer}`]);
    return{bookmark:camel(rows[0])};
   }
   case 'deleteHousehold':{
    if(input.confirmName!==context.membership.name)throw new ApiError(400,'Enter the household name exactly to confirm deletion.');
    const processing=await db.query("SELECT 1 FROM ingestion_jobs WHERE household_id=$1 AND status='processing' LIMIT 1",[hid]);
    if(processing.rows.length)throw new ApiError(409,'Wait for running ingestion to finish before deleting this household.');
    await db.query('DELETE FROM households WHERE id=$1',[hid]);return{ok:true};
   }
  }
 });
 if(email)await sendEmail(email.to,email.subject,email.text);
 if(input.action==='deleteHousehold')await deletePrivateHousehold(hid);
 return Response.json(result);
});
