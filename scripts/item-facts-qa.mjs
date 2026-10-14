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
 for(const question of ['What is my Aadhaar card serial number?',"What's my Aadhaar number?",'Show me the serial number of my Aadhar card']){
  const answer=(await post('/api/ask?householdId='+household,{question,operationId:randomUUID()})).response;
  assert.equal(answer.mode,'recorded-fact');assert.equal(answer.recordFacts[0].id,item.id);assert.equal(answer.recordFacts[0].value,expected);assert.equal(answer.confidence,'supported');
 }
 const answer=(await post('/api/ask?householdId='+household,{question:'What is my Aadhaar card model number?',operationId:randomUUID()})).response;
 assert.equal(answer.recordFacts[0].value,'Fixture model');
 console.log(JSON.stringify({passed:['live HTTP Aadhaar serial field','spelling and phrasing variations','exact string preservation','model field routing'],usedOnlyFictionalData:true}));
}finally{if(household)await pool.query('DELETE FROM households WHERE id=$1',[household]);if(actor)await pool.query('DELETE FROM "user" WHERE id=$1',[actor]);await pool.end();}
