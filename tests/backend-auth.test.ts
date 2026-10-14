import {afterAll,beforeAll,beforeEach,describe,expect,it} from 'vitest';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {createHmac,randomUUID} from 'node:crypto';
let auth:typeof import('../lib/auth').auth;
let pool:typeof import('../lib/db').pool;
let directory='';let userId='';let cookie='';
const origin=process.env.BETTER_AUTH_URL??'http://localhost:3000';
const email=`backend-journey-${randomUUID()}@example.invalid`;
const originalPassword=`Backend-test-${randomUUID()}`;
let password=originalPassword;
let testAddress='';
beforeEach(()=>{testAddress=`2001:db8:${randomUUID().replace(/-/g,'').slice(0,4)}:${randomUUID().replace(/-/g,'').slice(0,4)}::1`;});
const jar=(response:Response,previous='')=>{
 const entries=new Map(previous.split('; ').filter(Boolean).map(part=>{const index=part.indexOf('=');return[part.slice(0,index),part.slice(index+1)];}));
 for(const line of response.headers.getSetCookie()){const part=line.split(';')[0],index=part.indexOf('=');entries.set(part.slice(0,index),part.slice(index+1));}
 return Array.from(entries).filter(([,v])=>v).map(([k,v])=>`${k}=${v}`).join('; ');
};
async function endpoint(url:string,body?:Record<string,unknown>,cookies=cookie){return auth.handler(new Request(url.startsWith('http')?url:`${origin}/api/auth${url}`,{method:body?'POST':'GET',headers:{origin,cookie:cookies,'x-forwarded-for':testAddress,...(body?{'content-type':'application/json'}:{})},body:body?JSON.stringify(body):undefined}));}
async function mailLink(subject:string){
 const names=(await readdir(path.join(directory,'mail'))).sort().reverse();
 for(const name of names){const mail=JSON.parse(await readFile(path.join(directory,'mail',name),'utf8'));if(mail.to===email&&mail.subject===subject)return mail.text.match(/https?:\/\/\S+/)?.[0] as string;}
 throw new Error('Expected local email was not delivered');
}
function otp(uri:string){
 const key=new URL(uri).searchParams.get('secret')!;
 let bits='';for(const char of key.replace(/=/g,'').toUpperCase())bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(char).toString(2).padStart(5,'0');
 const bytes=Buffer.from((bits.match(/.{8}/g)??[]).map(byte=>parseInt(byte,2)));
 const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));
 const digest=createHmac('sha1',bytes).update(counter).digest(),offset=digest[digest.length-1]&15;
 return String((digest.readUInt32BE(offset)&0x7fffffff)%1000000).padStart(6,'0');
}
beforeAll(async()=>{
 directory=await mkdtemp(path.join(tmpdir(),'homeatlas-auth-'));
 process.env.DATA_DIR=directory;delete process.env.SMTP_HOST;
 process.env.BETTER_AUTH_SECRET??='local-backend-test-secret-32-characters';
 process.env.BETTER_AUTH_URL??=origin;
 ({auth}=await import('../lib/auth'));({pool}=await import('../lib/db'));
});
afterAll(async()=>{if(pool){if(userId)await pool.query('DELETE FROM "user" WHERE id=$1',[userId]);await pool.end();}if(directory)await rm(directory,{recursive:true,force:true});});
describe('real Better Auth account lifecycle through HTTP handlers',()=>{
 it('requires a real verification email link before allowing password sign-in',async()=>{
  const created=await endpoint('/sign-up/email',{name:'Backend Journey',email,password,callbackURL:'/'});expect(created.status).toBe(200);const data=await created.json();userId=data.user.id;
  expect(data.user.emailVerified).toBe(false);expect(created.headers.getSetCookie().some(value=>value.includes('session_token'))).toBe(false);
  const denied=await endpoint('/sign-in/email',{email,password});expect(denied.status).toBe(403);
  const verified=await endpoint(await mailLink('Verify your HomeAtlas email'));expect([200,302]).toContain(verified.status);cookie=jar(verified);
  const active=await endpoint('/get-session');expect(active.status).toBe(200);expect((await active.json()).user.emailVerified).toBe(true);
  const persisted=await pool.query('SELECT "emailVerified" FROM "user" WHERE id=$1',[userId]);expect(persisted.rows[0].emailVerified).toBe(true);
 });
 it('resets a password through the delivered one-use token and revokes old sessions',async()=>{
  const oldCookie=cookie;
  expect((await endpoint('/request-password-reset',{email,redirectTo:'/'})).status).toBe(200);
  const url=new URL(await mailLink('Reset your HomeAtlas password'));
  const token=url.pathname.split('/').at(-1)!;
  password=`Reset-backend-${randomUUID()}`;
  expect((await endpoint('/reset-password',{token,newPassword:password},'')).status).toBe(200);
  expect(await(await endpoint('/get-session',undefined,oldCookie)).json()).toBeNull();
  expect((await endpoint('/sign-in/email',{email,password:originalPassword},'')).status).toBe(401);
  expect((await endpoint('/reset-password',{token,newPassword:originalPassword},'')).status).toBe(400);
  const signed=await endpoint('/sign-in/email',{email,password},'');expect(signed.status).toBe(200);cookie=jar(signed);
 });
 it('lists active sessions and revokes other devices while retaining the current session',async()=>{
  const firstCookie=cookie;
  const second=await endpoint('/sign-in/email',{email,password},'');expect(second.status).toBe(200);cookie=jar(second);
  const sessions=await(await endpoint('/list-sessions')).json();expect(sessions.length).toBeGreaterThanOrEqual(2);
  expect((await endpoint('/revoke-other-sessions',{})).status).toBe(200);
  expect(await(await endpoint('/get-session',undefined,firstCookie)).json()).toBeNull();
  expect((await(await endpoint('/get-session')).json()).user.id).toBe(userId);
  const headers=second.headers.getSetCookie().join(';');expect(headers).toContain('HttpOnly');expect(headers).toContain('SameSite=Lax');
 });
 it('enrolls TOTP, challenges password sign-in, and accepts one-time recovery codes',async()=>{
  const enable=await endpoint('/two-factor/enable',{password});expect(enable.status).toBe(200);const setup=await enable.json();expect(setup.backupCodes).toHaveLength(10);
  const verified=await endpoint('/two-factor/verify-totp',{code:otp(setup.totpURI)});expect(verified.status).toBe(200);cookie=jar(verified,cookie);
  const active=await(await endpoint('/get-session')).json();expect(active.user.twoFactorEnabled).toBe(true);
  expect((await endpoint('/sign-out',{})).status).toBe(200);cookie='';
  const challenged=await endpoint('/sign-in/email',{email,password},'');expect(challenged.status).toBe(200);expect((await challenged.json()).twoFactorRedirect).toBe(true);cookie=jar(challenged);
  expect(await(await endpoint('/get-session')).json()).toBeNull();
  const recovered=await endpoint('/two-factor/verify-backup-code',{code:setup.backupCodes[0]});expect(recovered.status).toBe(200);cookie=jar(recovered,cookie);
  expect((await(await endpoint('/get-session')).json()).user.id).toBe(userId);
  await endpoint('/sign-out',{});cookie='';
  const challengedAgain=await endpoint('/sign-in/email',{email,password},'');cookie=jar(challengedAgain);
  expect((await endpoint('/two-factor/verify-backup-code',{code:setup.backupCodes[0]})).status).toBe(401);
  const validSecondCode=await endpoint('/two-factor/verify-backup-code',{code:setup.backupCodes[1]});expect(validSecondCode.status).toBe(200);cookie=jar(validSecondCode,cookie);
  const stored=await pool.query('SELECT secret,"backupCodes" FROM "twoFactor" WHERE "userId"=$1',[userId]);expect(stored.rows[0].backupCodes).not.toContain(setup.backupCodes[1]);expect(stored.rows[0].secret).not.toBe(new URL(setup.totpURI).searchParams.get('secret'));
 });
});
