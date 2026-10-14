import fs from 'node:fs/promises';
import {inflateRawSync} from 'node:zlib';
import path from 'node:path';
const directory=path.resolve('public/fonts');
const files=['Satoshi-Regular.woff2','Satoshi-Medium.woff2'];
if((await Promise.all([...files,'FFL.txt'].map(file=>fs.access(path.join(directory,file)).then(()=>true,()=>false)))).every(Boolean))process.exit(0);
// Official, unmodified webfonts for this website; source repos do not redistribute them.
const response=await fetch('https://api.fontshare.com/v2/fonts/download/satoshi');
if(!response.ok)throw new Error('Official Satoshi download failed. Retry setup when the network is available.');
const archive=Buffer.from(await response.arrayBuffer());
if(archive.length>10_000_000)throw new Error('Font archive exceeds the expected size.');
const end=archive.lastIndexOf(Buffer.from([0x50,0x4b,0x05,0x06]));
if(end<0)throw new Error('Invalid font archive.');
let cursor=archive.readUInt32LE(end+16);const entries=archive.readUInt16LE(end+10);
const wanted=new Map(files.map(file=>[`Satoshi_Complete/Fonts/WEB/fonts/${file}`,file]));wanted.set('Satoshi_Complete/License/FFL.txt','FFL.txt');
await fs.mkdir(directory,{recursive:true});
for(let i=0;i<entries;i++){
 if(archive.readUInt32LE(cursor)!==0x02014b50)throw new Error('Invalid font archive directory.');
 const method=archive.readUInt16LE(cursor+10),size=archive.readUInt32LE(cursor+20),nameLength=archive.readUInt16LE(cursor+28),extra=archive.readUInt16LE(cursor+30),comment=archive.readUInt16LE(cursor+32),offset=archive.readUInt32LE(cursor+42);
 const name=archive.subarray(cursor+46,cursor+46+nameLength).toString('utf8');
 if(wanted.has(name)){
  if(archive.readUInt32LE(offset)!==0x04034b50)throw new Error('Invalid font entry.');
  const start=offset+30+archive.readUInt16LE(offset+26)+archive.readUInt16LE(offset+28),compressed=archive.subarray(start,start+size);
  const data=method===0?compressed:method===8?inflateRawSync(compressed,{maxOutputLength:800_000}):null;
  if(!data)throw new Error('Unsupported font archive compression.');
  const target=path.join(directory,wanted.get(name));await fs.writeFile(target+'.tmp',data);await fs.rename(target+'.tmp',target);wanted.delete(name);
 }
 cursor+=46+nameLength+extra+comment;
}
if(wanted.size)throw new Error('Official archive did not contain the required fonts.');
console.log('Prepared official Satoshi Regular and Medium webfonts for local self-hosting.');
