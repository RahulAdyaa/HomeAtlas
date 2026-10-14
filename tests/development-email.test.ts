import { afterAll,beforeAll,describe,expect,it,vi } from 'vitest';
import { mkdtemp,rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createHash,randomUUID } from 'node:crypto';
import { localVerificationAvailable } from '../lib/development-email';
import { captureLocalEmail,sendEmail } from '../lib/email';

const origin='http://localhost:3000';
const users=[0,1].map(()=>({id:'',email:`local-mail-${randomUUID()}@example.invalid`,password:`Local-mail-${randomUUID()}`}));
let directory='';
let auth:typeof import('../lib/auth').auth;
let pool:typeof import('../lib/db').pool;
let route:typeof import('../app/api/development/verification/route');
const request=(body?:unknown,headers:Record<string,string>={},url=origin)=>new Request(`${url}/api/development/verification`,{
 method:body?'POST':'GET',headers:{origin,'content-type':'application/json',...headers},body:body?JSON.stringify(body):undefined,
});
beforeAll(async()=>{
 directory=await mkdtemp(path.join(tmpdir(),'homeatlas-local-mail-'));
 vi.stubEnv('NODE_ENV','development');vi.stubEnv('DATA_DIR',directory);vi.stubEnv('ALLOW_LOCAL_MAIL','true');
 vi.stubEnv('SMTP_HOST','');vi.stubEnv('BETTER_AUTH_URL',origin);
 process.env.BETTER_AUTH_SECRET??='local-backend-test-secret-32-characters';
 ({auth}=await import('../lib/auth'));({pool}=await import('../lib/db'));route=await import('../app/api/development/verification/route');
 for(const user of users){
  const response=await auth.handler(new Request(`${origin}/api/auth/sign-up/email`,{method:'POST',headers:{origin,'content-type':'application/json','x-forwarded-for':`2001:db8:${randomUUID().slice(0,4)}::1`},body:JSON.stringify({...user,name:'Local mail test',callbackURL:'/'})}));
  expect(response.status).toBe(200);user.id=(await response.json()).user.id;
 }
});
afterAll(async()=>{
 if(pool){
  for(const user of users){if(user.id)await pool.query('DELETE FROM "user" WHERE id=$1',[user.id]);await pool.query('DELETE FROM rate_limits WHERE key=$1',[`local-verification:${createHash('sha256').update(user.email).digest('hex')}`]);}
  await pool.end();
 }
 if(directory)await rm(directory,{recursive:true,force:true});vi.unstubAllEnvs();
});
describe('private local verification delivery',()=>{
 it('returns only availability through GET, never mailbox contents',async()=>{
  const response=await route.GET(request());expect(await response.json()).toEqual({available:true});
  expect(response.headers.get('cache-control')).toContain('no-store');
 });
 it('disables link retrieval in production, with SMTP, without opt-in and on non-loopback hosts',async()=>{
  for(const [key,value] of [['NODE_ENV','production'],['SMTP_HOST','smtp.example.test'],['ALLOW_LOCAL_MAIL','false']] as const){
   const previous=process.env[key]!;vi.stubEnv(key,value);
   expect(localVerificationAvailable(request())).toBe(false);expect((await route.POST(request(users[0]))).status).toBe(404);
   vi.stubEnv(key,previous);
  }
  expect(localVerificationAvailable(request(undefined,{},'http://example.test'))).toBe(false);
  expect(localVerificationAvailable(request(undefined,{host:'example.test'}))).toBe(false);
  expect(localVerificationAvailable(request(undefined,{'x-forwarded-host':'example.test'}))).toBe(false);
 });
 it('rejects cross-site requests even with valid account credentials',async()=>{
  expect((await route.POST(request(users[0],{origin:'https://other.example'}))).status).toBe(403);
  expect((await route.POST(request(users[0],{'sec-fetch-site':'cross-site'}))).status).toBe(403);
 });
 it('requires the recipient’s own password and returns identical errors for unknown accounts',async()=>{
  const wrong=await route.POST(request({email:users[0].email,password:users[1].password}));
  const other=await route.POST(request({email:users[1].email,password:users[0].password}));
  const absent=await route.POST(request({email:`missing-${randomUUID()}@example.invalid`,password:users[0].password}));
  for(const response of [wrong,other,absent]){expect(response.status).toBe(401);expect(await response.json()).toMatchObject({error:'Email or password is incorrect.'});}
 });
 it('keeps concurrent deliveries isolated and ignores messages to other recipients',async()=>{
  const [first,second]=await Promise.all([
   captureLocalEmail(users[0].email,async()=>{await sendEmail(users[1].email,'Unrelated','Other account');await sendEmail(users[0].email,'First','First account');}),
   captureLocalEmail(users[1].email,()=>sendEmail(users[1].email,'Second','Second account')),
  ]);
  expect(first).toMatchObject({to:users[0].email,text:'First account'});expect(second).toMatchObject({to:users[1].email,text:'Second account'});
 });
 it('opens a genuine auth link for only the password-validated unverified account',async()=>{
  const response=await route.POST(request({email:users[0].email.toUpperCase(),password:users[0].password,inviteToken:'a'.repeat(64)}));
  expect(response.status).toBe(200);expect(response.headers.get('cache-control')).toContain('no-store');
  const {url}=await response.json();const link=new URL(url);
  expect(link.origin).toBe(origin);expect(link.pathname).toBe('/api/auth/verify-email');expect(link.searchParams.get('callbackURL')).toBe('/?invite='+'a'.repeat(64));
  const verified=await auth.handler(new Request(url));expect([200,302]).toContain(verified.status);
  const statuses=await pool.query('SELECT id,"emailVerified" FROM "user" WHERE id=ANY($1)',[users.map(u=>u.id)]);
  expect(statuses.rows.find(u=>u.id===users[0].id).emailVerified).toBe(true);
  expect(statuses.rows.find(u=>u.id===users[1].id).emailVerified).toBe(false);
 });
 it('does not generate verification sign-in links for already verified accounts',async()=>{
  const response=await route.POST(request(users[0]));expect(response.status).toBe(409);expect(await response.json()).not.toHaveProperty('url');
 });
});
