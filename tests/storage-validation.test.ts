import {describe,expect,it} from 'vitest';
import {validateFile} from '../lib/storage';

const file=(name:string,type:string,bytes:Uint8Array)=>new File([bytes.slice().buffer as ArrayBuffer],name,{type});

describe('private upload format validation',()=>{
 it('accepts UTF-8 text, CSV, and XLSX/XLSM containers',async()=>{
  expect((await validateFile(file('notes.txt','text/plain',new TextEncoder().encode('Filter: six months')))).mime).toBe('text/plain');
  expect((await validateFile(file('records.csv','text/csv',new TextEncoder().encode('item,warranty\nwasher,2028')))).mime).toBe('text/csv');
  const signature=new Uint8Array([0x50,0x4b,0x03,0x04,0x14,0,0,0]);
  expect((await validateFile(file('records.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',signature))).extension).toBe('.xlsx');
  expect((await validateFile(file('records.xlsm','application/vnd.ms-excel.sheet.macroEnabled.12',signature))).mime).toBe('application/vnd.ms-excel.sheet.macroenabled.12');
 });

 it('accepts supported image and audio signatures and decoder-backed extensions',async()=>{
  const gif=await validateFile(file('label.gif','image/gif',new Uint8Array([...'GIF89a'].map(c=>c.charCodeAt(0)).concat([1,0,1,0]))),'image');
  expect(gif.mime).toBe('image/gif');
  const flac=await validateFile(file('voice.flac','audio/flac',new Uint8Array([...'fLaC'].map(c=>c.charCodeAt(0)).concat([0,0,0,0]))),'audio');
  expect(flac.mime).toBe('audio/flac');
  expect((await validateFile(file('photo.jp2','image/jp2',new Uint8Array([0,0,0,12])),'image')).extension).toBe('.jp2');
  expect((await validateFile(file('voice.wma','audio/x-ms-wma',new Uint8Array([1,2,3,4])),'audio')).mime).toBe('audio/x-ms-wma');
 });

 it('rejects spoofed formats, non-UTF-8 text, and the unsupported legacy XLS container',async()=>{
  await expect(validateFile(file('spoof.png','image/png',new TextEncoder().encode('not an image')))).rejects.toMatchObject({status:415});
  await expect(validateFile(file('broken.txt','text/plain',new Uint8Array([0xff,0xfe,0])))).rejects.toMatchObject({status:415});
  await expect(validateFile(file('old.xls','application/vnd.ms-excel',new Uint8Array([0xd0,0xcf,0x11,0xe0,0xa1,0xb1,0x1a,0xe1])))).rejects.toThrow('Save this workbook as .xlsx');
 });
});
