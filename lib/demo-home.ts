import {randomUUID,createHash} from 'node:crypto';
import type {DB} from './db';
import {writeOriginal} from './storage';
import {presetSize} from './home-layout';
// This is a transparent fixture, never represented as the user's own evidence.
export async function seedDemoHome(db:DB,householdId:string,actorId:string,files:string[]){
 if((await db.query("SELECT 1 FROM audit_events WHERE household_id=$1 AND action='demo.created'",[householdId])).rows.length)return {seeded:false};
 const layout=[
  {name:'Living room',kind:'living',color:'#f1decf',furniture:[['Sofa','sofa',-.9,-1],['Coffee table','table',-.6,.5],['TV unit','tv',1.5,-1.5]]},
  {name:'Kitchen',kind:'kitchen',color:'#dcead9',furniture:[['Kitchen counter','counter',-.6,-1.7],['Fridge','fridge',1.6,-1.5],['Dining table','table',0,.7]]},
  {name:'Bedroom',kind:'bedroom',color:'#e8ddf0',furniture:[['Bed','bed',-.7,-.7],['Wardrobe','wardrobe',1.5,-1.5],['Bedside cabinet','cabinet',-1.8,.8]]},
  {name:'Study',kind:'study',color:'#dce6f8',furniture:[['Desk','desk',-1.2,-1.3],['Chair','chair',-1.2,-.4],['Window area','window',-.8,-2.25],['Attached storage','storage',1.4,1.3]]},
  {name:'Bathroom',kind:'bathroom',color:'#d7ecec',furniture:[['Toilet','toilet',-1.4,-1.4],['Sink','sink',.8,-1.5],['Linen cabinet','cabinet',1.5,1]]},
  {name:'Laundry',kind:'laundry',color:'#f1ebd4',furniture:[['Washing machine','washer',-1,-1.4],['Utility sink','sink',.2,-1.4],['Supply cabinet','cabinet',1.4,-1.4]]},
 ];
 await db.query("UPDATE households SET name='My home' WHERE id=$1 AND lower(trim(name))='home1'",[householdId]);
 await db.query("UPDATE rooms SET name='Guest room' WHERE household_id=$1 AND lower(trim(name))='room2'",[householdId]);
 const zones:Record<string,string>={};
 const count=Number((await db.query("SELECT count(*) FROM locations WHERE household_id=$1 AND type='room'",[householdId])).rows[0].count);
 for(const [index,room] of layout.entries()){
  // Reuse an empty starter room; never move a room that already has custom zones.
  const existing=(await db.query("SELECT r.id FROM rooms r WHERE r.household_id=$1 AND r.name=$2 AND NOT EXISTS(SELECT 1 FROM locations l WHERE l.parent_id=r.id) ORDER BY r.created_at LIMIT 1",[householdId,room.name])).rows[0];
  const id=existing?.id||randomUUID();if(!existing)await db.query('INSERT INTO rooms(id,household_id,name,kind,color) VALUES($1,$2,$3,$4,$5)',[id,householdId,room.name,room.kind,room.color]);
  const slot=existing?index:count+index;
  await db.query('UPDATE locations SET color=$2,position=$3,size=$4,openings=$5 WHERE id=$1',[id,room.color,JSON.stringify({x:slot%3*5.3,y:0,z:Math.floor(slot/3)*5.3}),JSON.stringify({x:5,y:2.5,z:5}),JSON.stringify([{wall:'south',kind:'door',offset:.5,width:.9},{wall:'north',kind:'window',offset:.5,width:1.5}])]);
  for(const [name,preset,x,z] of room.furniture){const zid=randomUUID();zones[String(name)]=zid;await db.query('INSERT INTO locations(id,household_id,parent_id,name,type,preset,position,size,color,attached) VALUES($1,$2,$3,$4,\'zone\',$5,$6,$7,$8,$9)',[zid,householdId,id,name,preset,JSON.stringify({x,y:0,z}),JSON.stringify(presetSize(String(preset))),room.color,preset==='storage']);}
 }
 const drawer=randomUUID();await db.query("INSERT INTO locations(id,household_id,parent_id,name,type,preset,position,size,color) VALUES($1,$2,$3,'Top drawer','container','drawer','{\"x\":0.35,\"y\":0.4,\"z\":0}','{\"x\":0.6,\"y\":0.2,\"z\":0.45}','#a6bddc')",[drawer,householdId,zones.Desk]);
 const shelf=randomUUID();await db.query("INSERT INTO locations(id,household_id,parent_id,name,type,preset,position,size) VALUES($1,$2,$3,'Upper shelf','container','shelf','{\"x\":0,\"y\":0.8,\"z\":0}','{\"x\":0.8,\"y\":0.15,\"z\":0.3}')",[shelf,householdId,zones['Attached storage']]);
 for(const [title,location,text] of [
 ['SAMPLE — PAN card location',drawer,'Fictional demo record: the sample PAN card is kept in the top drawer of the desk in the Study. This is not a real identity document.'],
 ['SAMPLE — Home insurance folder',shelf,'Fictional demo record: the home insurance folder is on the upper shelf in the attached storage area of the Study. No real policy or coverage is represented.'],
 ['SAMPLE — Washing machine care',zones['Washing machine'],'Fictional demo checklist: inspect the washing machine filter monthly. Consult the real manufacturer manual before maintenance.'],
 ['SAMPLE — Fridge receipt',zones.Fridge,'Fictional demo receipt: a refrigerator was added to the sample kitchen. Purchase and warranty details are intentionally not real.'],
 ]){
  const source=randomUUID(),version=randomUUID(),bytes=Buffer.from('SAMPLE DATA — for demonstration only.\n\n'+text),sha256=createHash('sha256').update(bytes).digest('hex');
  await db.query("INSERT INTO sources(id,household_id,location_id,title,mime_type,status,created_by) VALUES($1,$2,$3,$4,'text/plain','ready',$5)",[source,householdId,location,title,actorId]);
  const file=await writeOriginal(householdId,source,version,{bytes,mime:'text/plain',extension:'.txt',sha256,name:title+'.txt'});files.push(file);
  await db.query("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES($1,$2,$3,1,$4,$5,$6,'text/plain')",[version,householdId,source,file,sha256,bytes.length]);
  await db.query('UPDATE sources SET current_version_id=$2 WHERE id=$1',[source,version]);
  const data=(await db.query('SELECT room_id,location_path FROM sources WHERE id=$1',[source])).rows[0];
  await db.query("INSERT INTO chunks(household_id,source_id,version_id,room_id,text,modality,metadata) VALUES($1,$2,$3,$4,$5,'text',$6)",[householdId,source,version,data.room_id,'Location: '+data.location_path+'\n\n'+bytes.toString(),JSON.stringify({sample:true,active:true,content_text:bytes.toString(),location_id:location,location_path:data.location_path,location_embedding_pending:true,extractor:'text'})]);
 }
 await db.query("INSERT INTO audit_events(household_id,actor_id,action,target_id) VALUES($1,$2,'demo.created',$3)",[householdId,actorId,householdId]);return {seeded:true};
}
