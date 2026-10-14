import { createHash } from 'node:crypto';
import { hashPassword,verifyPassword } from 'better-auth/crypto';
import { z } from 'zod';
import { auth } from '@/lib/auth';
import { pool } from '@/lib/db';
import { captureLocalEmail } from '@/lib/email';
import { localVerificationAvailable } from '@/lib/development-email';
import { api,ApiError,rateLimit } from '@/lib/server';

export const runtime='nodejs';
let dummyHash:Promise<string>|undefined;
export const GET=api(async(request)=>Response.json({available:localVerificationAvailable(request)}));

export const POST=api(async(request)=>{
 if(!localVerificationAvailable(request))throw new ApiError(404,'Not found.');
 await rateLimit('local-verification:all',30,60);
 const input=z.object({email:z.email().trim().toLowerCase(),password:z.string().min(10).max(128),inviteToken:z.string().regex(/^[a-f0-9]{64}$/).optional()}).parse(await request.json());
 const key=createHash('sha256').update(input.email).digest('hex');
 await rateLimit(`local-verification:${key}`,5,60);
 const {rows}=await pool.query('SELECT u."emailVerified",a.password FROM "user" u JOIN account a ON a."userId"=u.id AND a."providerId"=\'credential\' WHERE u.email=$1',[input.email]);
 dummyHash??=hashPassword('HomeAtlas-local-verification-dummy-password');
 const valid=await verifyPassword({hash:rows[0]?.password||await dummyHash,password:input.password});
 if(!rows[0]?.password||!valid)throw new ApiError(401,'Email or password is incorrect.');
 // Never mint a sign-in link for an already verified account (including accounts with 2FA).
 if(rows[0].emailVerified)throw new ApiError(409,'Your email is already verified. Use Continue to sign in.');
 const message=await captureLocalEmail(input.email,()=>auth.api.sendVerificationEmail({body:{email:input.email,callbackURL:input.inviteToken?'/?invite='+input.inviteToken:'/'}}));
 const link=message?.subject==='Verify your HomeAtlas email'?message.text.match(/https?:\/\/\S+/)?.[0]:undefined;
 if(!link)throw new ApiError(503,'The local verification email could not be opened. Please try again.');
 const url=new URL(link);
 if(url.origin!==new URL(process.env.BETTER_AUTH_URL??request.url).origin||url.pathname!=='/api/auth/verify-email')throw new ApiError(503,'The verification link is unavailable.');
 return Response.json({url:link});
});
