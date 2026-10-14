import {z} from 'zod';
import {api,ApiError,audit,scope,requireRole,uuid,shortText} from '@/lib/server';
import {pool,transaction,camel} from '@/lib/db';
import {presets} from '@/lib/locations';
export const runtime='nodejs';
const vector=z.object({x:z.number().finite().min(-100).max(100),y:z.number().finite().min(0).max(10),z:z.number().finite().min(-100).max(100)});
const size=z.object({x:z.number().min(.2).max(30),y:z.number().min(.1).max(5),z:z.number().min(.2).max(30)});
const fields={name:shortText,preset:z.enum(presets).default('area'),position:vector.default({x:0,y:0,z:0}),size:size.default({x:1.4,y:.8,z:1}),rotation:z.number().finite().min(-360).max(360).default(0),color:z.string().regex(/^#[\da-fA-F]{6}$/).default('#dce7f6'),icon:z.string().max(40).default('box'),attached:z.boolean().default(false),openings:z.array(z.object({wall:z.enum(['north','south','east','west']),kind:z.enum(['door','window']),offset:z.number().min(0).max(1),width:z.number().min(.3).max(3)})).max(12).default([])};
const inputSchema=z.discriminatedUnion('action',[
 z.object({action:z.literal('create'),parentId:uuid,type:z.enum(['room','zone','container']),...fields}),
 z.object({action:z.literal('update'),id:uuid,parentId:uuid,...fields}),
 z.object({action:z.literal('delete'),id:uuid}),
 z.object({action:z.literal('attach'),id:uuid,kind:z.enum(['source','item']),locationId:uuid}),
 z.object({action:z.literal('layout'),nodes:z.array(z.object({id:uuid,...fields})).max(400)}),
]);
export const GET=api(async request=>{const c=await scope(request);return Response.json({locations:(await pool.query('SELECT * FROM locations WHERE household_id=$1 ORDER BY created_at,id',[c.householdId])).rows.map(r=>camel(r))})});
export const POST=api(async request=>{
 const c=await scope(request);requireRole(c,['owner','editor']);const input=inputSchema.parse(await request.json());
 const result=await transaction(async db=>{
  const member=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2 FOR SHARE',[c.householdId,c.user.id])).rows[0];if(!member||member.role==='viewer')throw new ApiError(403,'Editor access required.');
  await db.query('SELECT id FROM households WHERE id=$1 FOR UPDATE',[c.householdId]);
  const get=async(id:string)=>{const n=(await db.query('SELECT * FROM locations WHERE id=$1 AND household_id=$2',[id,c.householdId])).rows[0];if(!n)throw new ApiError(404,'Location not found.');return n};
  const parent=async(type:string,id:string)=>{const p=await get(id);if(p.type!==({room:'home',zone:'room',container:'zone'} as Record<string,string>)[type])throw new ApiError(400,'Choose a valid parent: home → room → zone → container.');return p};
  const save=async(id:string,n:z.infer<typeof inputSchema>&any)=>{await db.query('UPDATE locations SET name=$3,preset=$4,position=$5,size=$6,rotation=$7,color=$8,icon=$9,attached=$10,openings=$11 WHERE id=$1 AND household_id=$2',[id,c.householdId,n.name,n.preset,JSON.stringify(n.position),JSON.stringify(n.size),n.rotation,n.color,n.icon,n.attached,JSON.stringify(n.openings)]);const node=await get(id);if(node.type==='room')await db.query('UPDATE rooms SET name=$3,color=$4 WHERE id=$1 AND household_id=$2',[id,c.householdId,n.name,n.color]);};
  let id='id' in input?input.id:undefined;
  if(input.action==='create'){
   await parent(input.type,input.parentId);
   if(input.type==='room'){id=(await db.query('INSERT INTO rooms(household_id,name,kind,color) VALUES($1,$2,$3,$4) RETURNING id',[c.householdId,input.name,'living',input.color])).rows[0].id;await save(id!,input)}
   else {id=(await db.query('INSERT INTO locations(household_id,parent_id,name,type) VALUES($1,$2,$3,$4) RETURNING id',[c.householdId,input.parentId,input.name,input.type])).rows[0].id;await save(id!,input)}
  } else if(input.action==='update'){const n=await get(input.id);if(n.type==='home')throw new ApiError(400,'Rename your home in settings.');await parent(n.type,input.parentId);await db.query('UPDATE locations SET parent_id=$3 WHERE id=$1 AND household_id=$2',[input.id,c.householdId,input.parentId]);await save(input.id,input);
  } else if(input.action==='layout'){for(const n of input.nodes){const old=await get(n.id);if(old.type==='home')throw new ApiError(400,'Home root cannot be resized.');await save(n.id,n)}
  } else if(input.action==='delete'){
   const n=await get(input.id);if(n.type==='home')throw new ApiError(400,'The home root cannot be removed here.');
   const used=(await db.query('SELECT 1 FROM locations WHERE parent_id=$1 UNION ALL SELECT 1 FROM sources WHERE location_id=$1 UNION ALL SELECT 1 FROM items WHERE location_id=$1 LIMIT 1',[input.id])).rows.length;
   if(used)throw new ApiError(409,'Move the documents, items and child locations before deleting this location.');
   if(n.type==='room'){const related=(await db.query('SELECT 1 FROM tasks WHERE room_id=$1 UNION ALL SELECT 1 FROM chunks WHERE room_id=$1 LIMIT 1',[input.id])).rows.length;if(related)throw new ApiError(409,'This room has historical records and cannot be deleted.');await db.query('DELETE FROM rooms WHERE id=$1 AND household_id=$2',[input.id,c.householdId])}
   await db.query('DELETE FROM locations WHERE id=$1 AND household_id=$2',[input.id,c.householdId]);
  } else if(input.action==='attach'){
   await get(input.locationId);const table=input.kind==='source'?'sources':'items';
   if(!(await db.query(`UPDATE ${table} SET location_id=$3 WHERE id=$1 AND household_id=$2 RETURNING id`,[input.id,c.householdId,input.locationId])).rows.length)throw new ApiError(404,'Record not found.');
  }
  await audit(db,c.householdId,c.user.id,'location.'+input.action,id);return {id};
 });return Response.json(result);
});
