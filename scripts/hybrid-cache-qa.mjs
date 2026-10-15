import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import pg from 'pg';
const origin='http://localhost:3000',pool=new pg.Pool({connectionString:process.env.DATABASE_URL});
let actor,household,cookie='';
async function post(url,data){const r=await fetch(origin+url,{method:'POST',headers:{origin,cookie,'content-type':'application/json'},body:JSON.stringify(data),signal:AbortSignal.timeout(30000)});const response=await r.json();if(!r.ok)throw new Error(`QA route ${url} returned ${r.status}`);return {response,r};}
try{
 const email=`facts-qa-${randomUUID()}@example.invalid`,password='Fixture-'+randomUUID();
 actor=(await post('/api/auth/sign-up/email',{name:'Item facts QA fixture',email,password})).response.user.id;
 await pool.query('UPDATE "user" SET "emailVerified"=true WHERE id=$1',[actor]);
 cookie=(await post('/api/auth/sign-in/email',{email,password})).r.headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
 household=(await post('/api/atlas',{action:'createHousehold',name:'Item facts QA fixture',starterRooms:false})).response.household.id;
 const url='/api/atlas?householdId='+household,expected='DEMO-00001234';
 const item=(await post(url,{action:'addItem',name:'aadhar card',serialNumber:expected,model:'Fixture model',make:'Fixture brand'})).response.item;
 const ask=async(question,extra={})=>(await post('/api/ask?householdId='+household,{question,operationId:randomUUID(),...extra})).response;
 const q='What is my Aadhaar card serial number?';
 const first=await ask(q);assert.equal(first.recordFacts[0].value,expected);assert.equal(first.cache.hit,false);
 const second=await ask(q);assert.equal(second.cache.kind,'exact');assert.equal(second.recordFacts[0].value,expected);
 const variant=await ask('Show me the serial number of my Aadhar card');assert.equal(variant.cache.kind,'semantic');assert.equal(variant.recordFacts[0].value,expected);
 const near=await ask('What is my Aadhaar card model number?');assert.equal(near.cache.hit,false);assert.equal(near.recordFacts[0].value,'Fixture model');
 const bypass=await ask(q,{bypassCache:true});assert.equal(bypass.cache.hit,false);
 const room=randomUUID();await pool.query("INSERT INTO rooms(id,household_id,name) VALUES($1,$2,'Bedroom')",[room,household]);
 await pool.query('UPDATE items SET location_id=$1,serial_number=$2 WHERE id=$3',[room,'DEMO-CHANGED',item.id]);
 const moved=await ask(q);assert.equal(moved.cache.hit,false);assert.equal(moved.recordFacts[0].value,'DEMO-CHANGED');assert.equal(moved.locationMatches[0].locationPath,'Bedroom');
 const clear=await fetch(origin+'/api/cache?householdId='+household,{method:'DELETE',headers:{origin,cookie}});assert.equal(clear.status,200);
 const afterClear=await ask(q);assert.equal(afterClear.cache.hit,false);
 const metrics=await fetch(origin+'/api/cache?householdId='+household,{headers:{cookie}});assert.equal(metrics.status,200);assert.ok((await metrics.json()).exactHitRate>0);
 console.log(JSON.stringify({passed:['live exact cache','live semantic cache','field near-miss rejection','bypass','move and field edit freshness','owner clear action','owner metrics'],usedOnlyFictionalData:true}));

}finally{if(household)await pool.query('DELETE FROM households WHERE id=$1',[household]);if(actor)await pool.query('DELETE FROM "user" WHERE id=$1',[actor]);await pool.end();}
