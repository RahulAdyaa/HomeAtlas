import { mkdir, writeFile, realpath, stat, rm } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID, createHash } from 'node:crypto';
import { ApiError } from './server';
export const storageRoot=path.resolve(/* turbopackIgnore: true */ process.env.STORAGE_ROOT??'.data/storage');
export const maxUploadBytes=Number(process.env.MAX_UPLOAD_BYTES??50*1024*1024);
export type ValidFile={bytes:Buffer,mime:string,extension:string,sha256:string,name:string};
const additionalRasterExtensions=new Set(['.apng','.blp','.bmp','.bufr','.bw','.cur','.dcx','.dds','.dib','.flc','.fli','.ftc','.ftu','.gbr','.grib','.h5','.hdf','.icb','.icns','.iim','.im','.j2c','.j2k','.jfif','.jp2','.jpf','.jpc','.jpe','.jpm','.jpx','.mj2','.msp','.palm','.pfm','.pgm','.pbm','.pcd','.pcx','.pnm','.ppm','.psd','.pxr','.qoi','.ras','.rgb','.rgba','.sgi','.tga','.vda','.vst','.xbm','.xpm']);
export async function validateFile(file:File,allowed:'all'|'image'|'audio'='all'):Promise<ValidFile>{
 if(file.size===0||file.size>maxUploadBytes)throw new ApiError(413,`Choose a file between 1 byte and ${Math.floor(maxUploadBytes/1024/1024)} MB.`);
 const bytes=Buffer.from(await file.arrayBuffer());
 const head=bytes.subarray(0,32),name=path.basename(file.name).replace(/[\r\n\u0000-\u001f]/g,'').slice(0,200)||'Untitled source';
 const suffix=path.extname(name).toLowerCase();let mime='',extension='';
 if(head.subarray(0,5).toString()==='%PDF-'){mime='application/pdf';extension='.pdf';}
 else if(head.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))){mime='image/png';extension='.png';}
 else if(head[0]===0xff&&head[1]===0xd8&&head[2]===0xff){mime='image/jpeg';extension='.jpg';}
 else if(head.subarray(0,6).toString()==='GIF87a'||head.subarray(0,6).toString()==='GIF89a'){mime='image/gif';extension='.gif';}
 else if(head.subarray(0,2).toString()==='BM'){mime='image/bmp';extension='.bmp';}
 else if(head.subarray(0,4).equals(Buffer.from([0x49,0x49,0x2a,0x00]))||head.subarray(0,4).equals(Buffer.from([0x4d,0x4d,0x00,0x2a]))){mime='image/tiff';extension='.tif';}
 else if(head.subarray(0,4).equals(Buffer.from([0x00,0x00,0x01,0x00]))){mime='image/x-icon';extension='.ico';}
 else if(head.subarray(0,4).toString()==='RIFF'&&head.subarray(8,12).toString()==='WEBP'){mime='image/webp';extension='.webp';}
 else if(head.subarray(0,4).toString()==='RIFF'&&head.subarray(8,12).toString()==='WAVE'){mime='audio/wav';extension='.wav';}
 else if(head.subarray(0,3).toString()==='ID3'||(head[0]===0xff&&(head[1]&0xe0)===0xe0&&(head[1]&0x18)!==0&&(((head[2]>>4)&0x0f)!==0)&&(((head[2]>>4)&0x0f)!==0x0f))){mime='audio/mpeg';extension='.mp3';}
 else if(head.subarray(0,4).toString()==='fLaC'){mime='audio/flac';extension='.flac';}
 else if(head.subarray(0,4).toString()==='FORM'&&['AIFF','AIFC'].includes(head.subarray(8,12).toString())){mime='audio/aiff';extension='.aiff';}
 else if(head.subarray(0,4).toString()==='OggS'){mime='audio/ogg';extension='.ogg';}
 else if(head.subarray(4,8).toString()==='ftyp'){mime=file.type.startsWith('audio/')||['.m4a','.m4b','.aac'].includes(suffix)?'audio/mp4':'video/mp4';extension=mime==='audio/mp4'?(suffix==='.aac'?'.aac':'.m4a'):'.mp4';}
 else if(head.subarray(0,4).equals(Buffer.from([0x1a,0x45,0xdf,0xa3]))){mime=file.type.startsWith('audio/')?'audio/webm':suffix==='.mkv'?'video/x-matroska':'video/webm';extension=mime==='video/x-matroska'?'.mkv':'.webm';}
 else if(head.subarray(0,4).toString()==='RIFF'&&head.subarray(8,12).toString()==='AVI '){mime='video/x-msvideo';extension='.avi';}
 else if(head[0]===0xff&&(head[1]===0xf1||head[1]===0xf9)){mime='audio/aac';extension='.aac';}
 else if(head.subarray(0,4).toString()==='FORM'){mime='audio/aiff';extension='.aiff';}
 else if(head.subarray(0,4).toString()==='caff'){mime='audio/x-caf';extension='.caf';}
 else if(head.subarray(0,5).toString()==='#!AMR'){mime='audio/amr';extension='.amr';}
 else if(head.subarray(0,4).toString()==='MThd'){mime='audio/midi';extension='.mid';}
 else if(head.subarray(0,16).equals(Buffer.from([0x30,0x26,0xb2,0x75,0x8e,0x66,0xcf,0x11,0xa6,0xd9,0x00,0xaa,0x00,0x62,0xce,0x6c]))){mime='audio/x-ms-wma';extension='.wma';}
 else if(head.subarray(0,4).toString()==='.snd'){mime='audio/basic';extension='.au';}
 else if(head.subarray(0,4).toString()==='PK\x03\x04'&&['.xlsx','.xlsm'].includes(suffix)){
  mime=suffix==='.xlsm'?'application/vnd.ms-excel.sheet.macroenabled.12':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';extension=suffix;
 }
 else if(head.subarray(0,8).equals(Buffer.from([0xd0,0xcf,0x11,0xe0,0xa1,0xb1,0x1a,0xe1]))&&suffix==='.xls')throw new ApiError(415,'Legacy .xls spreadsheets are not supported yet. Save this workbook as .xlsx and upload it again.');
 else if(additionalRasterExtensions.has(suffix)&&file.type.startsWith('image/')){mime=file.type.split(';')[0].toLowerCase();extension=suffix;}
 else if(/^\.[a-z0-9]{1,12}$/.test(suffix)&&file.type.toLowerCase().startsWith('audio/')){mime=file.type.split(';')[0].toLowerCase();extension=suffix;}
 else if((suffix==='.txt'||suffix==='.csv')&&bytes.subarray(0,Math.min(bytes.length,4096)).indexOf(0)===-1){
  try{new TextDecoder('utf-8',{fatal:true}).decode(bytes);mime=suffix==='.csv'?'text/csv':'text/plain';extension=suffix;}
  catch{throw new ApiError(415,'Text and CSV files must use UTF-8 encoding.');}
 }
 if(!mime)throw new ApiError(415,'Unsupported file. Use PDF, TXT, CSV, XLSX/XLSM, common image formats, audio, or video.');
 if(allowed==='image'&&!mime.startsWith('image/'))throw new ApiError(415,'Choose a supported image file.');
 if(allowed==='audio'&&!mime.startsWith('audio/'))throw new ApiError(415,'Choose a supported audio recording.');
 // Reject extension/magic mismatches, while allowing browsers to omit a MIME type.
 if(file.type&&file.type!=='application/octet-stream'){
  const normalized=file.type.split(';')[0].toLowerCase().replace('audio/x-wav','audio/wav').replace('audio/x-m4a','audio/mp4').replace('image/jpg','image/jpeg').replace('image/x-icon','image/x-icon').replace('application/vnd.ms-excel','application/vnd.ms-excel');
  const compatible=normalized===mime||(normalized==='audio/mp3'&&mime==='audio/mpeg')||(normalized==='audio/x-aiff'&&mime==='audio/aiff')||(normalized==='application/octet-stream')||(suffix==='.csv'&&normalized==='text/plain')||(suffix==='.txt'&&normalized==='text/plain')||(['.xlsx','.xlsm'].includes(suffix)&&normalized==='application/zip')||(suffix==='.au'&&normalized==='audio/basic')||(additionalRasterExtensions.has(suffix)&&normalized.startsWith('image/'))||(/^\.[a-z0-9]{1,12}$/.test(suffix)&&normalized.startsWith('audio/')&&mime.startsWith('audio/'));
  if(!compatible)throw new ApiError(415,'The file content does not match its declared type.');
 }
 return {bytes,mime,extension,sha256:createHash('sha256').update(bytes).digest('hex'),name};
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
