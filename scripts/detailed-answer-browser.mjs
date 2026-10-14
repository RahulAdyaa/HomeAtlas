import {chromium, expect} from '@playwright/test';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {browserExecutable} from './browser-runtime.mjs';
const origin='http://localhost:3000';
const browser=await chromium.launch({executablePath:browserExecutable(),headless:true});
const context=await browser.newContext({reducedMotion:'reduce'});
const account=JSON.parse(await fs.readFile('.data/journey-account.json'));
const errors=[];
try {
 const signed=await context.request.post(origin+'/api/auth/sign-in/email',{headers:{Origin:origin},data:account});
 expect(signed.ok()).toBe(true);
 const state=await (await context.request.get(origin+'/api/atlas')).json();
 const item=state.items.find(i=>i.name==='Bedroom air purifier');expect(item).toBeTruthy();
 const response=await context.request.post(origin+'/api/ask',{headers:{Origin:origin},multipart:{question:'Explain the replacement filter, replacement schedule and reset procedure for the AirOne AP-200 in detail.',itemId:item.id,operationId:crypto.randomUUID()},timeout:300000});
 expect(response.ok()).toBe(true);
 const reply=await response.json();expect(reply.mode).toBe('local-model-explained');expect(reply.answer).toContain('A200-HEPA');expect(reply.citations.length).toBeGreaterThan(0);
 await fs.writeFile('.data/detailed-answer-api.json',JSON.stringify(reply,null,2),{mode:0o600});
 for(const citation of reply.citations){
  const evidence=await (await context.request.get(origin+'/api/citations/'+citation.id)).json();expect(evidence.text).toContain(citation.text);
  const preview=await context.request.get(origin+'/api/citations/'+citation.id+'?preview=true');expect(preview.ok()).toBe(true);expect(preview.headers()['content-type']).toContain('image');
 }
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 // Replay the real verified API result to isolate rendering without another inference/charge.
 await page.route('**/api/ask',route=>route.fulfill({json:reply}));
 for(const viewport of [{width:1440,height:1050},{width:390,height:844}]){
  await page.setViewportSize(viewport);await page.goto(origin);
  if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:/Ask my home/}).click();
  await page.getByRole('textbox',{name:'Ask a question about your home'}).fill('Explain filter maintenance.');
  await page.getByRole('button',{name:'Ask my home',exact:true}).click();
  await expect(page.locator('.answer-content h3').first()).toBeVisible();
  await expect.poll(()=>page.locator('.answer-visual img').first().evaluate(img=>img.naturalWidth)).toBeGreaterThan(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.locator('.answer-visual').first().click();await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('button',{name:'Close evidence'}).click();
  console.log('PASS complete explanation, authorized page previews, evidence drawer, no overflow',viewport.width);
 }
 expect(errors).toEqual([]);
 console.log('PASS real detailed API response and independent citation checks');
}finally{await browser.close()}
