import nodemailer from 'nodemailer';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { AsyncLocalStorage } from 'node:async_hooks';
type LocalDelivery={to:string;subject:string;text:string};
const localDelivery=new AsyncLocalStorage<{to:string;message?:LocalDelivery}>();
// Capture only the email created by this request, never expose the shared mail spool.
export async function captureLocalEmail(to:string,send:()=>Promise<unknown>){
 const delivery:{to:string;message?:LocalDelivery}={to:to.toLowerCase()};
 await localDelivery.run(delivery,send);
 return delivery.message;
}
export async function sendEmail(to:string, subject:string, text:string) {
 if (process.env.SMTP_HOST) {
  const transport = nodemailer.createTransport({host:process.env.SMTP_HOST,port:Number(process.env.SMTP_PORT??1025),secure:process.env.SMTP_SECURE==='true',auth:process.env.SMTP_USER?{user:process.env.SMTP_USER,pass:process.env.SMTP_PASSWORD}:undefined});
  await transport.sendMail({from:process.env.SMTP_FROM??'HomeAtlas <hello@homeatlas.local>',to,subject,text});
 } else {
  if(process.env.NODE_ENV==='production' && process.env.ALLOW_LOCAL_MAIL!=='true') throw new Error('SMTP_HOST must be configured for email delivery');
  const directory=path.resolve(process.env.DATA_DIR??'.data','mail');
  await mkdir(directory,{recursive:true,mode:0o700});
  await writeFile(path.join(directory,`${Date.now()}-${randomUUID()}.json`),JSON.stringify({to,subject,text,createdAt:new Date().toISOString()},null,2),{mode:0o600});
  const delivery=localDelivery.getStore();
  if(delivery?.to===to.toLowerCase())delivery.message={to,subject,text};
 }
}
