import { mkdir, writeFile, realpath, stat, rm } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { ApiError } from './server';
export const storageRoot=path.resolve(/* turbopackIgnore: true */ process.env.STORAGE_ROOT??'.data/storage');
export const maxUploadBytes=Number(process.env.MAX_UPLOAD_BYTES??50*1024*1024);
export type ValidFile={bytes:Buffer,mime:string,extension:string,sha256:string,name:string};
export async function validateFile(file:File,allowed:'all'|'image'|'audio'='all'):Promise<ValidFile>{
 if(file.size===0||file.size>maxUploadBytes)throw new ApiError(413,`Choose a file between 1 byte and ${Math.floor(maxUploadBytes/1024/1024)} MB.`);
 const bytes=Buffer.from(await file.arrayBuffer());
 const head=bytes.subarray(0,32);let mime='',extension='';
 if(head.subarray(0,5).toString()==='%PDF-'){mime='application/pdf';extension='.pdf';}
 else if(head.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))){mime='image/png';extension='.png';}
 else if(head[0]===0xff&&head[1]===0xd8&&head[2]===0xff){mime='image/jpeg';extension='.jpg';}
 else if(head.subarray(0,4).toString()==='RIFF'&&head.subarray(8,12).toString()==='WEBP'){mime='image/webp';extension='.webp';}
 else if(head.subarray(0,4).toString()==='RIFF'&&head.subarray(8,12).toString()==='WAVE'){mime='audio/wav';extension='.wav';}
 else if(head.subarray(0,3).toString()==='ID3'||(head[0]===0xff&&(head[1]&0xe0)===0xe0)){mime='audio/mpeg';extension='.mp3';}
 else if(head.subarray(4,8).toString()==='ftyp'){mime=file.type.startsWith('audio/')?'audio/mp4':'video/mp4';extension=mime==='audio/mp4'?'.m4a':'.mp4';}
 else if(head.subarray(0,4).equals(Buffer.from([0x1a,0x45,0xdf,0xa3]))){mime=file.type.startsWith('audio/')?'audio/webm':'video/webm';extension='.webm';}
 else if(head.subarray(0,4).toString()==='OggS'){mime='audio/ogg';extension='.ogg';}
 if(!mime)throw new ApiError(415,'Unsupported file. Use PDF, JPEG, PNG, WebP, MP3, WAV, M4A, MP4, WebM, or OGG.');
 if(allowed==='image'&&!mime.startsWith('image/'))throw new ApiError(415,'Choose a JPEG, PNG, or WebP photo.');
 if(allowed==='audio'&&!mime.startsWith('audio/'))throw new ApiError(415,'Choose a supported audio recording.');
 // Reject extension/magic mismatches, while allowing browsers to omit a MIME type.
 if(file.type&&file.type!=='application/octet-stream'){
  const normalized=file.type.split(';')[0].replace('audio/x-wav','audio/wav').replace('audio/x-m4a','audio/mp4').replace('image/jpg','image/jpeg');
  if(normalized!==mime&&!(normalized==='audio/mp3'&&mime==='audio/mpeg'))throw new ApiError(415,'The file content does not match its declared type.');
 }
 return {bytes,mime,extension,sha256:createHash('sha256').update(bytes).digest('hex'),name:path.basename(file.name).replace(/[\r\n\u0000-\u001f]/g,'').slice(0,200)||'Untitled source'};
}
export async function writeOriginal(householdId:string,sourceId:string,versionId:string,file:ValidFile){
 const directory=path.join(storageRoot,'originals',householdId,sourceId);await mkdir(directory,{recursive:true,mode:0o700});
 const target=path.join(directory,versionId+file.extension);await writeFile(target,file.bytes,{flag:'wx',mode:0o600});return target;
}
export async function writeQueryMedia(householdId:string,file:ValidFile){
 const directory=path.join(storageRoot,'queries',householdId);await mkdir(directory,{recursive:true,mode:0o700});
 const target=path.join(directory,randomUUID()+file.extension);await writeFile(target,file.bytes,{flag:'wx',mode:0o600});return target;
}
export async function authorizedPath(storedPath:string){
 let resolved:string,root:string;
 try {resolved=await realpath(/* turbopackIgnore: true */ storedPath);root=await realpath(/* turbopackIgnore: true */ storageRoot);}catch{throw new ApiError(404,'Source file not found.');}
 if(!resolved.startsWith(root+path.sep))throw new ApiError(404,'Source file not found.');
 const info=await stat(resolved);if(!info.isFile())throw new ApiError(404,'Source file not found.');return{path:resolved,size:info.size};
}
export async function removePrivateFile(target:string){if(path.resolve(target).startsWith(storageRoot+path.sep))await rm(target,{force:true});}
export async function deletePrivateHousehold(householdId:string){
 // Only UUID-controlled tenant directories are passed to this function.
 if(!/^[a-f0-9-]{36}$/i.test(householdId))throw new Error('Invalid household ID');
 for(const category of ['originals','queries','derived'])await rm(path.join(/* turbopackIgnore: true */ storageRoot,category,householdId),{recursive:true,force:true});
}
