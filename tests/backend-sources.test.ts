import {afterAll,beforeAll,describe,expect,it} from 'vitest';
import {randomUUID,createHash} from 'node:crypto';
import {mkdtemp,readFile,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
let pool:typeof import('../lib/db').pool;
let storage:typeof import('../lib/storage');
let upload:typeof import('../app/api/sources/route');
let original:typeof import('../app/api/sources/[id]/route');
let retry:typeof import('../app/api/sources/[id]/retry/route');
let atlas:typeof import('../app/api/atlas/route');
let directory='',cookie='',actorId='',sourceId='',versionId='';
const home=randomUUID(),room=randomUUID(),item=randomUUID(),operationId=randomUUID();
const origin=process.env.BETTER_AUTH_URL??'http://localhost:3000';
let manual:Buffer,receipt:Buffer;
function form(bytes=manual,operation=operationId,source?:string){const body=new FormData();body.set('file',new File([new Uint8Array(bytes)],'HomeAtlas original fixture.pdf',{type:'application/pdf'}));body.set('operationId',operation);body.set('itemId',item);if(source)body.set('sourceId',source);return body;}
function request(body:FormData|Record<string,unknown>,route='/api/sources'){
 return new Request(`${origin}${route}?householdId=${home}`,{method:'POST',headers:{origin,cookie,...(body instanceof FormData?{}:{'content-type':'application/json'})},body:body instanceof FormData?body:JSON.stringify(body)});
}
function params(id:string){return{params:Promise.resolve({id})};}
function getRequest(id:string,suffix='',headers:Record<string,string>={}){return new Request(`${origin}/api/sources/${id}?householdId=${home}${suffix}`,{headers:{cookie,...headers}});}
beforeAll(async()=>{
 directory=await mkdtemp(path.join(tmpdir(),'homeatlas-sources-'));
 process.env.DATA_DIR=directory;process.env.STORAGE_ROOT=path.join(directory,'storage');
 process.env.BETTER_AUTH_SECRET??='backend-sources-only-secret-32-characters';
 process.env.BETTER_AUTH_URL??=origin;delete process.env.SMTP_HOST;
 ({pool}=await import('../lib/db'));storage=await import('../lib/storage');
 const{auth}=await import('../lib/auth');const password=`Source-tests-${randomUUID()}`,email=`source-tests-${randomUUID()}@example.invalid`;
 const user=await auth.api.signUpEmail({body:{name:'Source fixture owner',email,password}});actorId=user.user.id;
 await pool.query('UPDATE "user" SET "emailVerified"=true WHERE id=$1',[actorId]);
 const signed=await auth.api.signInEmail({body:{email,password},asResponse:true});cookie=signed.headers.getSetCookie().map(value=>value.split(';')[0]).join('; ');
 await pool.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3)',[home,'Source lifecycle fixture',actorId]);
 await pool.query("INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,'owner')",[home,actorId]);
 await pool.query("INSERT INTO rooms(id,household_id,name) VALUES($1,$2,'Bedroom')",[room,home]);
 await pool.query("INSERT INTO items(id,household_id,room_id,name) VALUES($1,$2,$3,'Air purifier')",[item,home,room]);
 manual=await readFile(new URL('./fixtures/AirOne-AP200-manual.pdf',import.meta.url));receipt=await readFile(new URL('./fixtures/AirOne-purchase-receipt.pdf',import.meta.url));
 upload=await import('../app/api/sources/route');original=await import('../app/api/sources/[id]/route');retry=await import('../app/api/sources/[id]/retry/route');atlas=await import('../app/api/atlas/route');
});
afterAll(async()=>{if(pool){await pool.query('DELETE FROM households WHERE id=$1',[home]);if(actorId)await pool.query('DELETE FROM "user" WHERE id=$1',[actorId]);await pool.end();}if(directory)await rm(directory,{recursive:true,force:true});});
describe('real private upload, source provenance, and reprocessing routes',()=>{
 it('rejects unsupported signatures, MIME mismatches, and non-images without reserving credits',async()=>{
  const body=form(Buffer.from('<script>unsafe</script>'),randomUUID());expect((await upload.POST(request(body))).status).toBe(415);
  await expect(storage.validateFile(new File([new Uint8Array(manual)],'wrong.png',{type:'image/png'}))).rejects.toMatchObject({status:415});
  await expect(storage.validateFile(new File([new Uint8Array(manual)],'manual.pdf',{type:'application/pdf'}),'image')).rejects.toMatchObject({status:415});
  const rows=await pool.query('SELECT id FROM credit_reservations WHERE household_id=$1',[home]);expect(rows.rows).toHaveLength(0);
 });
 it('accepts the M4A MIME alias without weakening signature checks',async()=>{
  const bytes=Buffer.concat([Buffer.from([0,0,0,24]),Buffer.from('ftypM4A '),Buffer.alloc(16)]);
  const file=await storage.validateFile(new File([bytes],'voice.m4a',{type:'audio/x-m4a'}),'audio');
  expect(file.mime).toBe('audio/mp4');expect(file.extension).toBe('.m4a');
  await expect(storage.validateFile(new File([new Uint8Array(manual)],'fake.m4a',{type:'audio/x-m4a'}),'audio')).rejects.toMatchObject({status:415});
 });
 it('uploads one immutable private original, inherits the item room, and deduplicates retrying the same operation',async()=>{
  const first=await upload.POST(request(form()));expect(first.status).toBe(202);const created=await first.json();sourceId=created.sourceId;versionId=created.versionId;
  const duplicate=await upload.POST(request(form()));expect(duplicate.status).toBe(202);expect((await duplicate.json()).sourceId).toBe(sourceId);
  expect((await upload.POST(request(form(receipt)))).status).toBe(409);
  const sources=await pool.query('SELECT * FROM sources WHERE household_id=$1',[home]);expect(sources.rows).toHaveLength(1);expect(sources.rows[0].room_id).toBe(room);
  const versions=await pool.query('SELECT * FROM source_versions WHERE source_id=$1',[sourceId]);expect(versions.rows).toHaveLength(1);expect(versions.rows[0].sha256).toBe(createHash('sha256').update(manual).digest('hex'));
  expect(versions.rows[0].storage_path).toContain(path.join('originals',home,sourceId));expect((await readFile(versions.rows[0].storage_path)).equals(manual)).toBe(true);
  const ledger=await pool.query("SELECT * FROM credit_ledger WHERE household_id=$1 AND operation_id=$2 AND kind='reservation'",[home,operationId]);expect(ledger.rows).toHaveLength(1);expect(ledger.rows[0].amount).toBe(5);
 });
 it('creates a new source version while old links continue to return identical bytes',async()=>{
  const added=await upload.POST(request(form(receipt,randomUUID(),sourceId)));expect(added.status).toBe(202);const current=await added.json();expect(current.versionId).not.toBe(versionId);
  const old=await original.GET(getRequest(sourceId,`&version=${versionId}`),params(sourceId));expect(old.status).toBe(200);expect(Buffer.from(await old.arrayBuffer()).equals(manual)).toBe(true);
  const latest=await original.GET(getRequest(sourceId),params(sourceId));expect(Buffer.from(await latest.arrayBuffer()).equals(receipt)).toBe(true);
  const metadata=await(await original.GET(getRequest(sourceId,'&metadata=true'),params(sourceId))).json();expect(metadata.versions.map((v:{version:number})=>v.version)).toEqual([2,1]);expect(JSON.stringify(metadata)).not.toContain(directory);
 });
 it('serves valid byte ranges and refuses a version belonging to another source',async()=>{
  const ranged=await original.GET(getRequest(sourceId,`&version=${versionId}`,{range:'bytes=0-4'}),params(sourceId));expect(ranged.status).toBe(206);expect(await ranged.text()).toBe('%PDF-');
  const invalid=await original.GET(getRequest(sourceId,'',{range:'bytes=999999999-'}),params(sourceId));expect(invalid.status).toBe(416);
  expect((await original.GET(getRequest(sourceId,`&version=${randomUUID()}`),params(sourceId))).status).toBe(404);
 });
 it('queues idempotent reprocessing for ready sources without changing their immutable source version',async()=>{
  const readySource=randomUUID(),readyVersion=randomUUID(),operation=randomUUID();
  const file=await storage.validateFile(new File([new Uint8Array(manual)],'ready.pdf',{type:'application/pdf'}));const stored=await storage.writeOriginal(home,readySource,readyVersion,file);
  await pool.query("INSERT INTO sources(id,household_id,title,mime_type,status,created_by) VALUES($1,$2,'Ready fixture','application/pdf','ready',$3)",[readySource,home,actorId]);
  await pool.query("INSERT INTO source_versions(id,household_id,source_id,version,storage_path,sha256,size_bytes,mime_type) VALUES($1,$2,$3,1,$4,$5,$6,'application/pdf')",[readyVersion,home,readySource,stored,file.sha256,manual.length]);
  await pool.query('UPDATE sources SET current_version_id=$1 WHERE id=$2',[readyVersion,readySource]);
  const first=await retry.POST(request({operationId:operation}),params(readySource));expect(first.status).toBe(202);const job=await first.json();
  const again=await retry.POST(request({operationId:operation}),params(readySource));expect(again.status).toBe(202);expect((await again.json()).jobId).toBe(job.jobId);
  const versions=await pool.query('SELECT id FROM source_versions WHERE source_id=$1',[readySource]);expect(versions.rows).toEqual([{id:readyVersion}]);
  const entries=await pool.query('SELECT id FROM ingestion_jobs WHERE household_id=$1 AND operation_id=$2',[home,operation]);expect(entries.rows).toHaveLength(1);
 });
 it('rejects nonexistent calendar dates and preserves valid dates independently of server timezone',async()=>{
  expect((await atlas.POST(request({action:'addTask',title:'Impossible date',dueDate:'2026-02-31'},'/api/atlas'))).status).toBe(400);
  const created=await atlas.POST(request({action:'addTask',title:'Replace filter',dueDate:'2026-10-30',itemId:item},'/api/atlas'));expect(created.status).toBe(200);expect((await created.json()).task.dueDate).toBe('2026-10-30');
 });
});
