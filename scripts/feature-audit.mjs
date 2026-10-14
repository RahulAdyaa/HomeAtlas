import {chromium, expect} from '@playwright/test';
import {browserExecutable} from './browser-runtime.mjs';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const origin = 'http://localhost:3000';
const browser = await chromium.launch({executablePath: browserExecutable(), headless: true, args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--use-file-for-fake-audio-capture='+path.resolve('tests/fixtures/plumber-note.wav')]});
const results = [], errors = [];
const context = await browser.newContext({storageState: '.data/journey-session.json', timezoneId: 'America/Los_Angeles', reducedMotion: 'reduce', permissions: ['microphone']});
const page = await context.newPage();
page.setDefaultTimeout(15000);
page.on('pageerror', e => errors.push(e.message));
const account = JSON.parse(await fs.readFile('.data/journey-account.json'));
const recipient = {name: 'Feature Audit Member', email: `feature-member-${Date.now()}@example.test`, password: crypto.randomBytes(18).toString('base64url')};
const memberContext = await browser.newContext({reducedMotion: 'reduce'});
const memberPage = await memberContext.newPage();
memberPage.setDefaultTimeout(15000); memberPage.on('pageerror', e => errors.push(e.message));
const headers = {Origin: origin};
let home, inviteUrl, memberId, memberHome;
async function check(name, run) {
  try { await run(); results.push({name, passed: true}); console.log('PASS', name); }
  catch (error) { results.push({name, passed: false, error: error.message}); console.log('FAIL', name, error.message.slice(0, 600)); }
}
async function nav(name, target=page) { await target.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name, exact: typeof name==='string'}).click(); }
async function post(ctx, data, household=home.household.id) { return ctx.request.post(origin+'/api/atlas?householdId='+household, {headers, data}); }
async function state(ctx=context, household) { const r=await ctx.request.get(origin+'/api/atlas'+(household?'?householdId='+household:'')); expect(r.ok()).toBe(true); return r.json(); }
async function mailLink(email, subject) {
  for(const name of (await fs.readdir('.data/mail')).sort().reverse()) { const m=JSON.parse(await fs.readFile('.data/mail/'+name)); if(m.to===email&&m.subject===subject)return m.text.match(/https?:\/\/\S+/)[0]; }
  throw new Error('Test email was not delivered');
}
function otp(uri) {
  let bits='';for(const char of new URL(uri).searchParams.get('secret').replace(/=/g,'').toUpperCase())bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(char).toString(2).padStart(5,'0');
  const key=Buffer.from((bits.match(/.{8}/g)||[]).map(byte=>parseInt(byte,2))),counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));
  const digest=crypto.createHmac('sha1',key).update(counter).digest(),offset=digest.at(-1)&15;return String((digest.readUInt32BE(offset)&0x7fffffff)%1000000).padStart(6,'0');
}
try {
  expect((await context.request.post(origin+'/api/auth/sign-in/email',{headers,data:account})).ok()).toBe(true);
  home=await state(); await page.goto(origin);
  await check('calendar dates retain their recorded day in a negative UTC offset', async () => {
    await nav(/^Maintenance/);
    const task=home.tasks.find(t=>!t.completedAt);
    await expect(page.locator('.maintenance-row').filter({hasText:task.title}).first().locator('.date-tile strong')).toHaveText(String(Number(task.dueDate.slice(8,10))));
  });
  await check('sending an invitation keeps the sender in the invitation form', async () => {
    await nav('Settings'); await page.getByRole('button',{name:'Invite someone',exact:true}).click();
    await page.getByLabel('Their email address').fill(recipient.email); await page.getByLabel('Their role').selectOption('viewer');
    await page.getByLabel('Your password (security check)').fill(account.password); await page.getByRole('button',{name:'Send invitation',exact:true}).click();
    const notice=page.getByText('Invitation link:',{exact:false}); await expect(notice).toBeVisible();
    inviteUrl=(await notice.innerText()).match(/https?:\/\/\S+/)[0];
    await expect(page.getByRole('heading',{name:'An invitation home.'})).toHaveCount(0);
    await expect(page.getByRole('dialog')).toHaveCount(1); await page.getByRole('button',{name:'Close',exact:true}).click();
  });
  await check('invitation rejects a different verified email', async () => {
    const r=await post(context,{action:'acceptInvite',token:new URL(inviteUrl).searchParams.get('invite')});expect(r.status()).toBe(404);
  });
  await check('new recipient retains invitation through signup and local email verification', async () => {
    await memberPage.goto(inviteUrl); await memberPage.getByRole('button',{name:'Create an account',exact:true}).click();
    await memberPage.getByLabel('Your name',{exact:true}).fill(recipient.name);await memberPage.getByLabel('Email address').fill(recipient.email);await memberPage.getByLabel('Password',{exact:true}).fill(recipient.password);
    await memberPage.getByRole('button',{name:'Create account',exact:true}).click();await expect(memberPage.getByText('Account created.',{exact:false})).toBeVisible();
    await memberPage.getByLabel('Password',{exact:true}).fill(recipient.password);await memberPage.getByRole('button',{name:'Open verification email',exact:true}).click();
    await memberPage.getByRole('button',{name:'Accept household invitation',exact:true}).click();
    await expect(memberPage.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
    const s=await state(memberContext);memberId=s.user.id;expect(s.household.id).toBe(home.household.id);expect(s.membership.role).toBe('viewer');
    expect((await post(memberContext,{action:'acceptInvite',token:new URL(inviteUrl).searchParams.get('invite')})).status()).toBe(404);
  });
  await check('viewer sees read-only controls and cannot mutate records or export owner data', async () => {
    await nav('Inventory',memberPage);await expect(memberPage.getByRole('button',{name:'Add an item',exact:true})).toHaveCount(0);
    await memberPage.getByRole('heading',{name:'Bedroom air purifier',exact:true,level:3}).click();await expect(memberPage.getByRole('button',{name:'Add document',exact:true})).toHaveCount(0);await memberPage.getByRole('button',{name:'Close',exact:true}).click();
    await nav('Settings',memberPage);await expect(memberPage.getByRole('link',{name:'Export data',exact:true})).toHaveCount(0);
    expect((await post(memberContext,{action:'addRoom',name:'Denied room'})).status()).toBe(403);
    expect((await memberContext.request.get(origin+'/api/export')).status()).toBe(403);
    expect((await memberContext.request.post(origin+'/api/sources',{headers,multipart:{file:{name:'manual.pdf',mimeType:'application/pdf',buffer:await fs.readFile('tests/fixtures/AirOne-AP200-manual.pdf')}}})).status()).toBe(403);
  });
  await check('owner changes a member to editor through the security form', async () => {
    await page.reload();await nav('Settings');await page.getByLabel('Role for '+recipient.name).selectOption('editor');await page.getByLabel('Your password (security check)').fill(account.password);await page.getByRole('button',{name:'Update role',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);
    await memberPage.reload();await nav('Inventory',memberPage);await expect(memberPage.getByRole('button',{name:'Add an item',exact:true})).toBeVisible();
    const r=await post(memberContext,{action:'addRoom',name:'Shared audit room'});expect(r.ok()).toBe(true);
  });
  await check('inventory edit, search, and room filter persist correctly', async () => {
    await nav('Inventory');await page.getByRole('heading',{name:'Bedroom air purifier',exact:true,level:3}).click();await page.getByRole('button',{name:'Edit details',exact:true}).click();await page.getByLabel('Notes',{exact:true}).fill('Original fictional sample. Updated by the feature audit.');await page.getByRole('button',{name:'Save to my home',exact:true}).click();
    await page.getByRole('textbox',{name:'Search inventory'}).fill('No item matches this');await expect(page.locator('.item-card')).toHaveCount(0);await page.getByRole('textbox',{name:'Search inventory'}).fill('AP-200');await expect(page.locator('.item-card')).toHaveCount(1);
    expect((await state()).items.find(i=>i.id===home.items[0].id).notes).toContain('Updated by the feature audit');
  });
  await check('voice form sends the selected item and releases microphone on navigation', async () => {
    await page.getByRole('heading',{name:'Bedroom air purifier',exact:true,level:3}).click();await page.getByRole('button',{name:'Ask about this item',exact:true}).click();
    let submitted;
    // Transport stub verifies browser form scope; real Whisper/RAG runs separately in media-check.mjs.
    await page.route('**/api/ask', async route=>{submitted=route.request().postDataBuffer().toString();await route.fulfill({json:{answer:'Voice form transport fixture',citations:[],mode:'abstention',confidence:'insufficient',transcription:'Scoped voice question'}})});
    await page.getByRole('button',{name:'Record a voice note',exact:true}).click();await page.waitForTimeout(1200);await page.getByRole('button',{name:'Finish recording',exact:true}).click();await page.getByRole('button',{name:/Ask from recording/}).click();await expect(page.locator('.answer-card')).toContainText('Voice form transport fixture');expect(submitted).toContain('name="itemId"');expect(submitted).toContain(home.items[0].id);await page.unroute('**/api/ask');
    await page.evaluate(()=>{const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=async c=>{const stream=await original(c);window.auditStream=stream;return stream}});
    await page.getByRole('button',{name:'Record a voice note',exact:true}).click();await expect(page.getByRole('button',{name:'Finish recording',exact:true})).toBeVisible();await nav('Overview');await expect.poll(()=>page.evaluate(()=>window.auditStream.getTracks().every(t=>t.readyState==='ended'))).toBe(true);
  });
  await check('long saved searches and saved-answer question provenance', async () => {
    await nav('Ask my home ASK');const long='Which replacement filter matches the AirOne AP-200? '+ 'Please check the household records. '.repeat(6);await page.getByRole('textbox',{name:'Ask a question about your home'}).fill(long);await page.getByRole('button',{name:'Save search',exact:true}).click();await expect(page.getByText('Search saved for later.',{exact:true})).toBeVisible();
    const saved=(await state()).bookmarks.find(b=>b.question===long);expect(saved.title).toBe(long.slice(0,160).trim());
    const original=home.bookmarks.find(b=>b.answer);await page.locator('.saved-answers .library-row').filter({hasText:original.title}).first().click();await page.getByRole('textbox',{name:'Ask a question about your home'}).fill('A different unsent question');await page.getByRole('button',{name:'Save this answer',exact:true}).click();await expect(page.getByText('Answer saved to bookmarks.',{exact:true})).toBeVisible();
    const latest=(await state()).bookmarks[0];expect(latest.question).toBe(original.question);expect(latest.answer).toBe(original.answer);
  });
  await check('recurring completion creates exactly one next reminder and item history', async () => {
    const taskTitle='Audit recurring reminder '+Date.now();const r=await post(context,{action:'addTask',title:taskTitle,dueDate:'2026-10-24',recurrenceDays:30,itemId:home.items[0].id});expect(r.ok()).toBe(true);const task=(await r.json()).task;
    await page.reload();await nav(/^Maintenance/);await page.getByRole('button',{name:'Complete '+taskTitle,exact:true}).click();await expect(page.getByText('Done. Your next reminder is scheduled.',{exact:true})).toBeVisible();
    const s=await state();const next=s.tasks.filter(t=>t.title===task.title&&!t.completedAt);expect(next).toHaveLength(1);expect(next[0].dueDate).toBe('2026-11-23');expect(s.history.some(h=>h.taskId===task.id)).toBe(true);expect((await post(context,{action:'completeTask',id:task.id})).status()).toBe(404);
  });
  await check('owner JSON export, CSV download, health and last-owner guard', async () => {
    await nav('Settings');await expect(page.getByText('Household health',{exact:true})).toBeVisible();
    const exported=await context.request.get(origin+'/api/export');expect(exported.ok()).toBe(true);const json=await exported.json();expect(json.householdId).toBe(home.household.id);expect(JSON.stringify(json)).not.toContain('storagePath');expect(json.source_versions.length).toBeGreaterThan(0);
    await nav('Credits & usage');const download=page.waitForEvent('download');await page.getByRole('link',{name:'Export CSV',exact:true}).click();const file=await download;expect(file.suggestedFilename()).toBe('homeatlas-credits.csv');
    expect((await post(context,{action:'removeMember',userId:home.user.id,password:account.password})).status()).toBe(409);
  });
  await check('existing multi-household member accepts an invite into the correct household', async () => {
    const created=await post(memberContext,{action:'createHousehold',name:'Disposable member home',starterRooms:false});expect(created.ok()).toBe(true);memberHome=(await created.json()).household.id;
    const invite=await post(context,{action:'invite',email:recipient.email,role:'editor',password:account.password});expect(invite.ok()).toBe(true);
    await memberPage.goto((await invite.json()).inviteUrl);await memberPage.getByRole('button',{name:'Accept invitation',exact:true}).click();await expect(memberPage).toHaveURL(new RegExp('householdId='+home.household.id));
    await nav('Settings',memberPage);await memberPage.getByLabel('Switch household').selectOption(memberHome);await expect(memberPage.locator('.household-switch strong')).toHaveText('Disposable member home');
  });
  await check('revoking a member removes access to household and private sources', async () => {
    await nav('Settings');await page.getByRole('button',{name:'Remove '+recipient.name,exact:true}).click();await page.getByLabel('Your password (security check)').fill(account.password);await page.getByRole('button',{name:'Remove access',exact:true}).click();await expect(page.getByLabel('Role for '+recipient.name)).toHaveCount(0);
    expect((await memberContext.request.get(origin+'/api/atlas?householdId='+home.household.id)).status()).toBe(404);expect((await memberContext.request.get(origin+'/api/sources/'+home.sources[0].id+'?householdId='+home.household.id)).status()).toBe(404);await memberPage.goto(origin+'/?householdId='+home.household.id);await expect(memberPage.locator('.household-switch strong')).toHaveText('Disposable member home');
  });
  await check('sign-out clears prior answer state before another account signs in', async () => {
    await nav('Ask my home ASK');await page.locator('.saved-answers .library-row').filter({hasText:home.bookmarks.find(b=>b.answer).title}).first().click();await expect(page.locator('.answer-card')).toBeVisible();await nav('Settings');await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByRole('button',{name:'Sign in',exact:true}).first().click();await page.getByLabel('Email address').fill(recipient.email);await page.getByLabel('Password',{exact:true}).fill(recipient.password);await page.getByRole('button',{name:'Continue',exact:true}).click();await nav('Ask my home ASK');await expect(page.locator('.answer-card')).toHaveCount(0);await expect(page.getByRole('textbox',{name:'Ask a question about your home'})).toHaveValue('');
  });
  await check('forgot-password email, reset form, old-session revocation and new login', async () => {
    await nav('Settings');await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByRole('button',{name:'Sign in',exact:true}).first().click();await page.getByRole('button',{name:'Forgot password?',exact:true}).click();await page.getByLabel('Email address').fill(recipient.email);await page.getByRole('button',{name:'Send reset link',exact:true}).click();await expect(page.getByText('If an account exists, a reset link has been sent.',{exact:true})).toBeVisible();
    const link=await mailLink(recipient.email,'Reset your HomeAtlas password');await page.goto(link);await page.getByLabel('New password',{exact:true}).fill('Reset-'+crypto.randomUUID());const newPassword=await page.getByLabel('New password',{exact:true}).inputValue();await page.getByRole('button',{name:'Reset password',exact:true}).click();await expect(page.getByText('Password updated. You can sign in.',{exact:true})).toBeVisible();expect((await memberContext.request.get(origin+'/api/atlas')).status()).toBe(401);
    await page.getByLabel('Email address').fill(recipient.email);await page.getByLabel('Password',{exact:true}).fill(newPassword);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();recipient.password=newPassword;await page.reload();await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
  });
  await check('authenticator setup, login challenge, recovery code and disable work through UI', async () => {
    await nav('Settings');await page.getByRole('button',{name:'Set up',exact:true}).click();await page.getByLabel('Your password',{exact:true}).fill(recipient.password);await page.getByRole('button',{name:'Get setup key',exact:true}).click();const uri=await page.getByLabel('Authenticator setup URI').inputValue();const recovery=await page.locator('.recovery-codes code').first().innerText();await page.getByLabel('Code from your authenticator').fill(otp(uri));await page.getByRole('button',{name:'Verify & finish',exact:true}).click();await expect(page.getByRole('button',{name:'Manage',exact:true})).toBeVisible();
    await page.getByRole('button',{name:'Sign out',exact:true}).click();await page.getByRole('button',{name:'Sign in',exact:true}).first().click();await page.getByLabel('Email address').fill(recipient.email);await page.getByLabel('Password',{exact:true}).fill(recipient.password);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.getByLabel('Authenticator code')).toBeVisible();await page.getByRole('button',{name:'Use a recovery code',exact:true}).click();await page.getByLabel('Recovery code').fill(recovery);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
    await nav('Settings');await page.getByRole('button',{name:'Manage',exact:true}).click();await page.getByLabel('Your password',{exact:true}).fill(recipient.password);await page.getByRole('button',{name:'Disable two-factor authentication',exact:true}).click();await expect(page.getByRole('button',{name:'Set up',exact:true})).toBeVisible();
  });
  await check('household deletion removes only the disposable test household', async () => {
    await nav('Settings');await page.getByRole('button',{name:'Delete household',exact:true}).click();await page.getByLabel('Type “Disposable member home” to confirm').fill('Disposable member home');await page.getByLabel('Your password',{exact:true}).fill(recipient.password);await page.getByRole('button',{name:'Permanently delete household',exact:true}).click();await expect(page.getByRole('button',{name:'Create my home',exact:true})).toBeVisible();expect((await state(context)).household).toBeNull();
  });
} finally {
  await fs.writeFile('.data/feature-audit-report.json',JSON.stringify({date:new Date().toISOString(),results,browserErrors:errors},null,2),{mode:0o600});
  await browser.close();
}
console.log(`${results.filter(r=>r.passed).length}/${results.length} feature checks passed; ${errors.length} browser exceptions`);
if(results.some(r=>!r.passed)||errors.length)process.exitCode=1;
