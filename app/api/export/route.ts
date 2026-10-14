import { api,scope,requireRole,audit } from '@/lib/server';
import { transaction,camel } from '@/lib/db';
export const runtime='nodejs';
export const GET=api(async(request)=>{
 const context=await scope(request);requireRole(context,['owner']);
 const output=await transaction(async(db)=>{
  await db.query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');
  const membership=(await db.query('SELECT role FROM memberships WHERE household_id=$1 AND user_id=$2',[context.householdId,context.user.id])).rows[0];if(membership?.role!=='owner')throw new Error('Permission changed');
  const data:Record<string,unknown>={format:'HomeAtlas household export',version:2,exportedAt:new Date().toISOString(),householdId:context.householdId};
  for(const table of ['locations','rooms','items','tasks','maintenance_events','sources','source_versions','chunks','conversations','messages','bookmarks','credit_ledger','audit_events']){
   // Table names are a server-owned allowlist, never request data.
   const{rows}=await db.query(`SELECT * FROM ${table} WHERE household_id=$1`,[context.householdId]);
   data[table]=rows.map(row=>{delete row.storage_path;delete row.image_path;delete row.embedding;delete row.image_embedding;return camel(row);});
  }
  data.household=camel((await db.query('SELECT * FROM households WHERE id=$1',[context.householdId])).rows[0]);
  data.members=(await db.query('SELECT m.role,u.name,u.email FROM memberships m JOIN "user" u ON u.id=m.user_id WHERE household_id=$1',[context.householdId])).rows;
  data.originalFiles='Original files remain available through the authenticated /api/sources/{sourceId}?version={versionId} endpoint. Download them before deleting the household.';
  await audit(db,context.householdId,context.user.id,'Exported household data');return data;
 });
 return new Response(JSON.stringify(output,null,2),{headers:{'Content-Type':'application/json','Content-Disposition':'attachment; filename="homeatlas-export.json"'}});
});
