import {chromium,expect} from '@playwright/test';
import {browserExecutable} from './browser-runtime.mjs';
import fs from 'node:fs/promises';

const base='http://localhost:3000';
const browser=await chromium.launch({executablePath:browserExecutable(),headless:true});
const failures=[],checks=[];
const viewports=[{width:390,height:844},{width:768,height:1024},{width:1024,height:900},{width:1440,height:1050}];
const navigation=['Overview','My home','Inventory','Document library','Ask my home','Maintenance','Credits & usage','Settings'];
const record=(name)=>{checks.push(name);console.log('PASS',name)};
async function monitoredContext(options){
 const context=await browser.newContext(options);

 const page=await context.newPage();
 page.on('pageerror',error=>failures.push(`Browser exception: ${error.message}`));
 page.on('console',message=>{if(message.type()==='error'&&!message.text().includes('401 (Unauthorized)'))failures.push(`Console ${new URL(message.location().url||base).pathname}: ${message.text()}`)});
 page.on('response',response=>{if(response.status()>=400){const pathname=new URL(response.url()).pathname;if(response.status()===401&&pathname==='/api/atlas')return;failures.push(`HTTP ${response.status()} ${pathname}`)}});
 page.on('requestfailed',request=>{if(request.failure()?.errorText==='net::ERR_ABORTED')return;failures.push(`Network failure: ${new URL(request.url()).pathname}`)});
 await page.goto(base);await page.locator('.loading-screen').waitFor({state:'hidden'});await page.evaluate(()=>document.fonts.ready);
 await page.addScriptTag({path:'node_modules/axe-core/axe.min.js'});return {context,page};
}
async function audit(page,name){
 await page.evaluate(()=>document.fonts.ready);
 const violations=await page.evaluate(async()=>{return(await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(item=>({id:item.id,nodes:item.nodes.map(node=>({target:node.target,summary:node.failureSummary}))}))});
 if(violations.length)failures.push(`${name}: ${JSON.stringify(violations)}`);
 const bounds=await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth,font:document.fonts.check('400 16px Satoshi')&&document.fonts.check('500 16px Satoshi'),family:getComputedStyle(document.body).fontFamily}));
 if(bounds.width>bounds.viewport)failures.push(`${name}: horizontal overflow ${bounds.width}/${bounds.viewport}`);
 if(!bounds.font||!bounds.family.includes('Satoshi'))failures.push(`${name}: required Satoshi fonts unavailable`);
 if(!violations.length&&bounds.width<=bounds.viewport&&bounds.font)record(`${name}: axe, fonts, overflow`);
}
async function nav(page,name){
 if(page.viewportSize().width<701)await page.getByRole('button',{name:'Open navigation',exact:true}).click();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))}).click();
}
try{
 for(const viewport of viewports){
  const {context,page}=await monitoredContext({viewport,reducedMotion:'reduce'});
  await expect(page.getByRole('heading',{name:'Your home. On the record.',exact:true})).toBeVisible();
  await audit(page,`Landing ${viewport.width}px reduced motion`);
  const reduced=await page.evaluate(()=>Array.from(document.querySelectorAll('[data-reveal],.mission-word')).every(element=>Number(getComputedStyle(element).opacity)===1));
  expect(reduced).toBe(true);record(`Landing ${viewport.width}px: reduced-motion content visible`);
  await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
  await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Skip to content',exact:true})).toBeFocused();await page.keyboard.press('Enter');await expect(page.locator('#main-content')).toBeFocused();record(`Landing ${viewport.width}px: skip link`);
  for(let i=0;i<5;i++){
   const button=page.locator(`#capability-trigger-${i}`);await button.click();
   await expect(button).toHaveAttribute('aria-expanded','true');await expect(page.locator(`#capability-body-${i}`)).toBeVisible();await audit(page,`Capability ${i+1} ${viewport.width}px`);
  }
  const inventory=await page.evaluate(()=>Array.from(document.querySelectorAll('[data-placeholder]')).every(element=>element.closest('section')?.querySelector('.sample-footnote')));
  expect(inventory).toBe(true);record(`Landing ${viewport.width}px: disclosures and placeholder register`);
  await page.getByRole('button',{name:'Make yourself at home',exact:true}).click();await audit(page,`Signup dialog ${viewport.width}px`);await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button',{name:'Toggle theme',exact:true}).click();await audit(page,`Landing ${viewport.width}px with dark app preference`);await page.getByRole('button',{name:'Make yourself at home',exact:true}).click();await audit(page,`Signup dialog ${viewport.width}px dark`);await page.keyboard.press('Escape');await page.getByRole('button',{name:'Toggle theme',exact:true}).click();
  if(viewport.width===1440||viewport.width===390){await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.screenshot({path:`docs/screenshots/redesign-landing-${viewport.width===1440?'desktop':'phone'}.png`,fullPage:true});}
  await context.close();
 }
 // Native scroll + a single GSAP/Lenis loop; both ends must remain usable.
 for(const viewport of viewports){
  const {context,page}=await monitoredContext({viewport,reducedMotion:'no-preference'});
  await page.waitForFunction(()=>document.querySelector('.atlas-landing')?.dataset.motion==='ready');
  const stage=await page.locator('.hero-stage').boundingBox();expect(Math.abs(stage.height/viewport.height-3)).toBeLessThan(.05);
  await audit(page,`Landing ${viewport.width}px animated initial state`);
  const start=await page.locator('.hero-device').evaluate(element=>new DOMMatrix(getComputedStyle(element).transform).a);expect(start).toBeCloseTo(.6,1);
  await page.evaluate(()=>window.scrollTo({top:document.querySelector('.hero-stage').offsetHeight-innerHeight,behavior:'instant'}));
  await page.waitForFunction(()=>Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('.hero-device')).transform).a-1)<.01);
  const chassis=await page.locator('.device-chassis').evaluate(element=>Number(getComputedStyle(element).opacity));expect(chassis).toBe(0);
  for(const section of ['.records-field','.capability-section','.mission-section','.care-section','.closing-section']){await page.locator(section).scrollIntoViewIfNeeded();await page.waitForTimeout(450);}
  const stranded=await page.evaluate(()=>Array.from(document.querySelectorAll('[data-reveal]')).filter(element=>Number(getComputedStyle(element).opacity)<.99).length);expect(stranded).toBe(0);
  await audit(page,`Landing ${viewport.width}px animated final state`);record(`Landing ${viewport.width}px: 300svh hero, full-size final device, no stranded reveals`);
  await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>!document.querySelector('.atlas-landing')?.dataset.motion);record(`Landing ${viewport.width}px: live reduced-motion change cleans up timeline`);
  await context.close();
 }
 // A preference change during count-up must restore the exact authored number.
 {const {context,page}=await monitoredContext({viewport:viewports[3],reducedMotion:'no-preference'});await page.waitForFunction(()=>document.querySelector('.atlas-landing')?.dataset.motion==='ready');await page.locator('[data-counter]').first().scrollIntoViewIfNeeded();await page.waitForTimeout(100);await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>!document.querySelector('.atlas-landing')?.dataset.motion);const exact=await page.evaluate(()=>Array.from(document.querySelectorAll('[data-counter]')).every(element=>element.textContent===element.dataset.counter));expect(exact).toBe(true);record('Live reduced motion during count-up: authored values restored');await context.close();}
 // Refresh the fictional fixture once; all viewport contexts share that fresh session.
 const fixture=JSON.parse(await fs.readFile('.data/journey-account.json','utf8'));
 if(!fixture.email.startsWith('homeatlas-journey-')||!fixture.email.endsWith('@example.test'))throw new Error('QA requires the original fictional journey fixture.');
 const fixtureContext=await browser.newContext();let signed;
 for(let attempt=0;attempt<3;attempt++){signed=await fixtureContext.request.post(base+'/api/auth/sign-in/email',{headers:{origin:base},data:{email:fixture.email,password:fixture.password}});if(signed.status()!==429)break;const delay=Math.min(61,Math.max(1,Number(signed.headers()['retry-after'])||61));console.log(`Waiting ${delay}s for the fixture authentication rate limit.`);await new Promise(resolve=>setTimeout(resolve,delay*1000));}
 expect(signed.status()).toBe(200);const fixtureState=await fixtureContext.storageState();await fixtureContext.close();
 for(const viewport of viewports){
  const {context,page}=await monitoredContext({viewport,reducedMotion:'reduce',storageState:fixtureState});
  await expect(page.locator('nav[aria-label="Main navigation"]')).toBeAttached();
  for(const name of navigation){await nav(page,name);await audit(page,`${name} ${viewport.width}px light`);}
  await page.getByRole('button',{name:'Toggle theme',exact:true}).click();
  for(const name of navigation){await nav(page,name);await audit(page,`${name} ${viewport.width}px dark`);}
  await nav(page,'Ask my home');
  if(await page.locator('.saved-answers .library-row').count()){
   await page.locator('.saved-answers .library-row').first().click();await page.locator('.evidence-card').first().click();await expect(page.getByRole('dialog')).toBeVisible();await audit(page,`Evidence viewer ${viewport.width}px dark`);await page.getByRole('button',{name:'Close evidence',exact:true}).click();
  }
  if(viewport.width<701){await page.getByRole('button',{name:'Open navigation',exact:true}).click();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Open navigation',exact:true})).toBeFocused();record(`App ${viewport.width}px: mobile navigation escape and focus return`);}
  await nav(page,'My home');await page.getByRole('button',{name:'Explore in 3D',exact:true}).click();await expect(page.locator('.scene-canvas canvas')).toBeVisible();
  await page.getByRole('button',{name:'Rotate home left',exact:true}).focus();await page.keyboard.press('Enter');await page.getByRole('button',{name:'Reset home view',exact:true}).click();record(`App ${viewport.width}px: 3D keyboard controls`);
  await audit(page,`3D Home View ${viewport.width}px dark`);
  if(viewport.width===1440||viewport.width===390){await nav(page,'Overview');await page.getByRole('button',{name:'Toggle theme',exact:true}).click();await page.screenshot({path:`docs/screenshots/redesign-dashboard-${viewport.width===1440?'desktop':'phone'}.png`,fullPage:true});}
  await context.close();
 }
}catch(error){failures.push(error.message||String(error))}finally{
 await browser.close();await fs.mkdir('.data',{recursive:true});await fs.writeFile('.data/design-qa-report.json',JSON.stringify({date:new Date().toISOString(),checks,failures},null,2),{mode:0o600});
}
if(failures.length){console.error(`FAIL — ${failures.length} failures`);for(const failure of failures)console.error(failure);process.exitCode=1}else console.log(`PASS — 0 failures (${checks.length} checks)`);
