import {request, expect} from '@playwright/test';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
// Original scan fixture is generated locally; no user files are read or changed.
execFileSync('worker/.venv/bin/python',['-c',"import fitz; d=fitz.open(); p=d.new_page(width=600,height=780); p.insert_image(p.rect,filename='tests/fixtures/filter-page-photo.png'); d.save('.data/audit-scan.pdf'); d.close()"]);
const origin='http://localhost:3000',headers={Origin:origin};
const context=await request.newContext({baseURL:origin,storageState:'.data/journey-session.json',extraHTTPHeaders:headers});
const results=[];let hid;
async function check(name,run){try{await run();results.push({name,passed:true});console.log('PASS',name)}catch(e){results.push({name,passed:false,error:e.message});console.log('FAIL',name,e.message.slice(0,500))}}
const endpoint=p=>p+(p.includes('?')?'&':'?')+'householdId='+hid;
async function atlas(){const r=await context.get(endpoint('/api/atlas'));expect(r.ok()).toBe(true);return r.json()}
async function action(data){const r=await context.post(endpoint('/api/atlas'),{data});expect(r.ok()).toBe(true);return r.json()}
async function upload(name,mime,buffer,extra={}){const r=await context.post(endpoint('/api/sources'),{multipart:{file:{name,mimeType:mime,buffer},operationId:crypto.randomUUID(),...extra}});expect(r.status()).toBe(202);return r.json()}
async function status(id,wanted){await expect.poll(async()=>{const s=(await atlas()).sources.find(s=>s.id===id);if(s?.status==='failed'&&wanted!=='failed')throw new Error(s.error);return s?.status},{timeout:180000,intervals:[1000,2000,3000]}).toBe(wanted)}
let broken,firstVersion,imageSource,scanSource,imageItem,scanItem;
try{
 hid=(await action({action:'createHousehold',name:'Disposable ingestion audit',starterRooms:false})).household.id;
 await check('unsupported uploads fail without charging credits',async()=>{
  const bad=await context.post(endpoint('/api/sources'),{multipart:{file:{name:'fake.pdf',mimeType:'application/pdf',buffer:Buffer.from('<script>invalid</script>')}}});expect(bad.status()).toBe(415);
  expect((await atlas()).credits.available).toBe(100);
 });
 await check('corrupt PDF becomes failed and releases its full reservation',async()=>{
  broken=await upload('corrupt-original.pdf','application/pdf',Buffer.from('%PDF-1.7\nnot a valid PDF'));firstVersion=broken.versionId;await status(broken.sourceId,'failed');const a=await atlas();expect(a.credits.available).toBe(100);expect(a.credits.reserved).toBe(0);expect(a.credits.ledger.filter(l=>l.kind==='refund')).toHaveLength(1);
 });
 await check('failed-source retry also refunds once and can recover with a new valid version',async()=>{
  const r=await context.post(endpoint('/api/sources/'+broken.sourceId+'/retry'),{data:{operationId:crypto.randomUUID()}});expect(r.status()).toBe(202);await status(broken.sourceId,'failed');expect((await atlas()).credits.available).toBe(100);
  const next=await upload('corrected-manual.pdf','application/pdf',await fs.readFile('tests/fixtures/AirOne-AP200-manual.pdf'),{sourceId:broken.sourceId});await status(next.sourceId,'ready');expect((await atlas()).credits.available).toBe(95);
  const old=await context.get(endpoint('/api/sources/'+broken.sourceId+'?version='+firstVersion));expect(await old.text()).toBe('%PDF-1.7\nnot a valid PDF');
 });
 await check('reprocessing retains old source versions and settles exactly one charge',async()=>{
  const op=crypto.randomUUID();for(let i=0;i<2;i++)expect((await context.post(endpoint('/api/sources/'+broken.sourceId+'/retry'),{data:{operationId:op}})).status()).toBe(202);await status(broken.sourceId,'ready');expect((await atlas()).credits.available).toBe(90);
  const metadata=await(await context.get(endpoint('/api/sources/'+broken.sourceId+'?metadata=true'))).json();expect(metadata.versions).toHaveLength(2);
 });
 await check('standalone image OCR and scanned PDF both reach ready through the real queue',async()=>{
  imageItem=(await action({action:'addItem',name:'Image-only test appliance'})).item.id;scanItem=(await action({action:'addItem',name:'Scanned-only test appliance'})).item.id;
  imageSource=await upload('filter-photo.png','image/png',await fs.readFile('tests/fixtures/filter-page-photo.png'),{itemId:imageItem});await status(imageSource.sourceId,'ready');
  scanSource=await upload('scanned-manual.pdf','application/pdf',await fs.readFile('.data/audit-scan.pdf'),{itemId:scanItem});await status(scanSource.sourceId,'ready');expect((await atlas()).credits.available).toBe(80);
 });
 for(const kind of ['image','scan'])await check(kind+'-only retrieval produces grounded OCR citations and previews',async()=>{
  const source=kind==='image'?imageSource:scanSource,op=crypto.randomUUID();const body={question:'Which replacement filter fits the AirOne AP-200?',itemId:kind==='image'?imageItem:scanItem,operationId:op};
  const before=(await atlas()).credits.available;const r=await context.post(endpoint('/api/ask'),{data:body,timeout:180000});expect(r.status()).toBe(200);const reply=await r.json();expect(reply.mode).toBe('local-model-grounded');expect(reply.answer).toContain('A200-HEPA');expect(reply.citations.length).toBeGreaterThan(0);
  for(const c of reply.citations){expect(c.sourceId).toBe(source.sourceId);expect(c.versionId).toBe(source.versionId);const canonical=await(await context.get(endpoint('/api/citations/'+c.id))).json();expect(canonical.text).toContain(c.text);expect((await context.get(endpoint('/api/citations/'+c.id+'?preview=true'))).status()).toBe(200)}
  const replay=await context.post(endpoint('/api/ask'),{data:body});expect((await replay.json()).replayed).toBe(true);expect((await atlas()).credits.available).toBe(before-1);
 });
 await check('an item without records cannot retrieve another item’s evidence',async()=>{
  const item=(await action({action:'addItem',name:'No records appliance'})).item.id;const r=await context.post(endpoint('/api/ask'),{data:{question:'Which replacement filter fits the AirOne AP-200?',itemId:item,operationId:crypto.randomUUID()},timeout:180000});expect(r.ok()).toBe(true);const reply=await r.json();expect(reply.mode).toBe('abstention');expect(reply.citations).toHaveLength(0);
 });
 await check('ledger reconciles all charges and refunds with zero stranded reservations',async()=>{const a=await atlas();expect(a.credits.reserved).toBe(0);expect(a.credits.ledger.reduce((n,l)=>n+l.availableDelta,0)).toBe(a.credits.available)});
}finally{
 if(hid){const r=await context.post(endpoint('/api/atlas'),{data:{action:'deleteHousehold',confirmName:'Disposable ingestion audit',password:JSON.parse(await fs.readFile('.data/journey-account.json')).password}});if(!r.ok())console.log('Disposable household cleanup failed',r.status())}
 await fs.writeFile('.data/ingestion-audit-report.json',JSON.stringify({date:new Date().toISOString(),results},null,2),{mode:0o600});await context.dispose();
}
console.log(`${results.filter(r=>r.passed).length}/${results.length} ingestion checks passed`);if(results.some(r=>!r.passed))process.exitCode=1;
