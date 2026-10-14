import {chromium,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';
import {browserExecutable} from './browser-runtime.mjs';
const browser=await chromium.launch({executablePath:browserExecutable(),headless:true});
const errors=[];
try{
 for(const viewport of [{width:1440,height:1050},{width:390,height:844}]){
  const context=await browser.newContext({viewport});const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  const email=`verification-ui-${randomUUID()}@example.invalid`,password=`Verify-ui-${randomUUID()}`;
  await page.goto('http://localhost:3000');
  await page.getByRole('button',{name:'Make yourself at home'}).click();
  await page.getByLabel('Your name',{exact:true}).fill('Verification Test');
  await page.getByLabel('Email address').fill(email);await page.getByLabel('Password',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Create account',exact:true}).click();
  await expect(page.getByText('Account created.',{exact:false})).toBeVisible();
  await expect(page.getByLabel('Email address')).toHaveValue(email);
  await page.getByLabel('Password',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Open verification email',exact:true}).click();
  await expect(page.getByRole('button',{name:'Create my home',exact:true})).toBeVisible();
  const session=await(await page.request.get('http://localhost:3000/api/auth/get-session')).json();
  expect(session.user.email).toBe(email);expect(session.user.emailVerified).toBe(true);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await context.close();console.log(`PASS local signup → verification button → signed-in onboarding at ${viewport.width}px`);
 }
 expect(errors).toEqual([]);
}finally{await browser.close()}
