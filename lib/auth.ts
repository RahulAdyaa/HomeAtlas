import { betterAuth } from 'better-auth';
import { twoFactor } from 'better-auth/plugins';
import { passkey } from '@better-auth/passkey';
import { pool } from './db';
import { sendEmail } from './email';
const baseURL=process.env.BETTER_AUTH_URL??'http://localhost:3000';
export const auth = betterAuth({
 appName:'HomeAtlas', baseURL, secret:process.env.BETTER_AUTH_SECRET,
 database:pool, trustedOrigins:[baseURL],
 emailAndPassword:{enabled:true,requireEmailVerification:true,minPasswordLength:10,maxPasswordLength:128,revokeSessionsOnPasswordReset:true,
  sendResetPassword:async({user,url})=>sendEmail(user.email,'Reset your HomeAtlas password',`Use this one-time link to reset your password: ${url}\nIf you did not request this, ignore this message.`)},
 emailVerification:{sendOnSignUp:true,sendOnSignIn:true,autoSignInAfterVerification:true,expiresIn:3600,
  sendVerificationEmail:async({user,url})=>sendEmail(user.email,'Verify your HomeAtlas email',`Welcome to HomeAtlas. Verify your email: ${url}`)},
 session:{expiresIn:60*60*24*14,updateAge:60*60*24,freshAge:60*15,cookieCache:{enabled:false}},
 rateLimit:{enabled:true,window:60,max:50,storage:'database'},
 advanced:{useSecureCookies:baseURL.startsWith('https://'),defaultCookieAttributes:{httpOnly:true,sameSite:'lax'}},
 plugins:[twoFactor({issuer:'HomeAtlas'}),passkey({rpID:new URL(baseURL).hostname,rpName:'HomeAtlas',origin:baseURL})],
});
