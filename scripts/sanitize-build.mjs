import fs from 'node:fs/promises';import path from 'node:path';
const root=path.resolve('.next/standalone');
await fs.cp('public',path.join(root,'public'),{recursive:true});
await fs.cp('.next/static',path.join(root,'.next','static'),{recursive:true});
// Next standalone copies environment files separately from route tracing. Provision secrets at runtime.
for(const name of await fs.readdir(root))if(/^\.env(?:$|\.)/.test(name))await fs.unlink(path.join(root,name));
const forbidden=[];async function walk(dir){for(const entry of await fs.readdir(dir,{withFileTypes:true})){if(entry.isSymbolicLink())continue;const full=path.join(dir,entry.name);if(['.data','.venv'].includes(entry.name)||/^\.env(?:$|\.)/.test(entry.name)||['tiny.pt','journey-session.json','verification.dump'].includes(entry.name))forbidden.push(full);if(entry.isDirectory())await walk(full)}}await walk(root);if(forbidden.length)throw new Error('Private runtime artifacts were included in the build: '+forbidden.join(', '));console.log('PASS standalone artifact contains no environment secrets, private data, or model weights.');
