import {chromium} from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
export function browserExecutable(){
 if(process.env.PLAYWRIGHT_EXECUTABLE_PATH)return process.env.PLAYWRIGHT_EXECUTABLE_PATH;
 const bundled=chromium.executablePath();if(fs.existsSync(bundled))return bundled;
 // Reuse an installed compatible Playwright browser on macOS instead of downloading another copy.
 if(process.platform==='darwin'){
  const root=path.join(os.homedir(),'Library','Caches','ms-playwright');
  if(fs.existsSync(root))for(const name of fs.readdirSync(root).filter(n=>/^chromium-\d+$/.test(n)).sort().reverse()){
   const candidate=path.join(root,name,'chrome-mac-arm64','Google Chrome for Testing.app','Contents','MacOS','Google Chrome for Testing');if(fs.existsSync(candidate))return candidate;
  }
 }
 return undefined;
}
