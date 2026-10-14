import {spawn} from 'node:child_process';
import net from 'node:net';
import {once} from 'node:events';
import {setTimeout as delay} from 'node:timers/promises';
import {chromium,expect} from '@playwright/test';
import {browserExecutable} from './browser-runtime.mjs';
const listener=net.createServer();listener.listen(0,'127.0.0.1');await once(listener,'listening');const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
const child=spawn(process.execPath,['.next/standalone/server.js'],{env:{...process.env,NODE_ENV:'production',PORT:String(port),HOSTNAME:'127.0.0.1'},stdio:'ignore'});
const stopped=once(child,'exit');let browser;
try{
 const base='http://127.0.0.1:'+port;let ready=false;
 for(let i=0;i<120;i++){if(child.exitCode!==null)throw new Error('Production server exited during startup');try{ready=(await fetch(base)).ok}catch{}if(ready)break;await delay(250)}
 expect(ready).toBe(true);const html=await(await fetch(base)).text();const assets=[...new Set([...html.matchAll(/(?:src|href)="(\/_next\/static\/[^"?]+)/g)].map(m=>m[1]))];expect(assets.length).toBeGreaterThan(0);
 for(const asset of assets)expect((await fetch(base+asset)).ok).toBe(true);
 expect((await(await fetch(base+'/api/health')).json()).status).toBe('ok');expect((await(await fetch(base+'/api/development/verification')).json()).available).toBe(false);
 expect((await fetch(base+'/api/atlas')).status).toBe(401);
 browser=await chromium.launch({executablePath:browserExecutable(),headless:true});const page=await browser.newPage({reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base);await expect(page.getByRole('button',{name:'Make yourself at home',exact:true})).toBeVisible();await page.evaluate(()=>document.fonts.ready);expect(await page.evaluate(()=>document.fonts.check('400 16px Satoshi'))).toBe(true);
 await page.getByRole('button',{name:'Make yourself at home',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByLabel('Email address')).toBeVisible();expect(errors).toEqual([]);
 console.log(`PASS standalone runtime: ${assets.length} assets, health, private-route denial, disabled development verification, fonts and hydrated signup dialog; zero browser exceptions.`);
}finally{if(browser)await browser.close();if(child.exitCode===null)child.kill('SIGTERM');await stopped;console.log('Temporary production server stopped.');}
