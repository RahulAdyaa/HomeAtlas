// Actual authentication -> multipart upload -> durable queue -> hybrid RAG -> canonical citation.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import pg from 'pg';
const origin='http://localhost:3000',pool=new pg.Pool({connectionString:process.env.DATABASE_URL});
let actor,household,cookie='';const checks=[];
async function request(path,method='GET',body){const multipart=body instanceof FormData;const r=await fetch(origin+path,{method,headers:{origin,cookie,...(!multipart&&body?{'content-type':'application/json'}:{})},body:body?(multipart?body:JSON.stringify(body)):undefined,signal:AbortSignal.timeout(300000)});const data=await r.json();if(!r.ok)throw new Error(`QA route returned ${r.status}`);return {r,data};}
try{
 const email=`image-qa-${randomUUID()}@example.invalid`,password='Fixture-'+randomUUID();
 actor=(await request('/api/auth/sign-up/email','POST',{name:'Fictional image QA',email,password})).data.user.id;
 await pool.query('UPDATE "user" SET "emailVerified"=true WHERE id=$1',[actor]);
 cookie=(await request('/api/auth/sign-in/email','POST',{email,password})).r.headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
 household=(await request('/api/atlas','POST',{action:'createHousehold',name:'Fictional image QA',starterRooms:false})).data.household.id;
 const scope=path=>path+'?householdId='+household;
 for(const [name,type] of [['rotated-card.png','image/png'],['mixed.pdf','application/pdf']]){
  const item=(await request(scope('/api/atlas'),'POST',{action:'addItem',name:'Fictional image record '+name})).data.item;
  const form=new FormData();form.set('file',new File([await readFile('.data/image-evidence-qa/'+name)],name,{type}));form.set('itemId',item.id);form.set('operationId',randomUUID());
  const upload=(await request(scope('/api/sources'),'POST',form)).data;
  let ready=false;
  for(let i=0;i<120;i++){
   const source=(await request(scope('/api/atlas'))).data.sources.find(s=>s.id===upload.sourceId);
   if(source?.status==='failed')throw new Error('Image ingestion failed');
   if(source?.status==='ready'){ready=true;break;}await new Promise(r=>setTimeout(r,1000));
  }
  assert.ok(ready,'ingestion must finish');console.log('Ingestion ready:',name);
  const reply=(await request(scope('/api/ask'),'POST',{question:'What is the serial number shown on the uploaded Aadhaar card?',itemId:item.id,operationId:randomUUID(),bypassCache:true})).data;
  assert.equal(reply.confidence,'supported');assert.ok(reply.answer.includes('DEMO-00001234'));
  assert.ok(reply.citations.length>0&&reply.citations.every(c=>c.sourceId===upload.sourceId));
  for(const citation of reply.citations){const canonical=(await request(scope('/api/citations/'+citation.id))).data;assert.ok(canonical.text.includes(citation.text));}
  checks.push({case:name,exactField:true,canonicalCitations:true,mode:reply.mode});console.log('Grounded answer passed:',name);
 }
 await writeFile('evaluation/image-live-results.json',JSON.stringify({fictionalOnly:true,checks},null,2));
 console.log(JSON.stringify({passed:checks,usedOnlyFictionalData:true}));
}finally{if(household)await pool.query('DELETE FROM households WHERE id=$1',[household]);if(actor)await pool.query('DELETE FROM "user" WHERE id=$1',[actor]);await pool.end();}
