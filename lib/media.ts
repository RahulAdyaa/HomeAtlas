import { createReadStream } from 'node:fs';
import { Readable } from 'node:stream';
import { authorizedPath } from './storage';
import { ApiError } from './server';
export async function privateMedia(request:Request,storedPath:string,mime:string,title:string){
 const file=await authorizedPath(storedPath);const headers=new Headers({'Content-Type':mime,'Content-Disposition':`inline; filename*=UTF-8''${encodeURIComponent(title)}`,'X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'",'Accept-Ranges':'bytes','Cache-Control':'private, no-store'});
 const range=request.headers.get('range');let start=0,end=file.size-1,status=200;
 if(range){const match=/^bytes=(\d*)-(\d*)$/.exec(range);if(!match||(!match[1]&&!match[2]))throw new ApiError(416,'Invalid media range.');
  if(!match[1])start=Math.max(0,file.size-Number(match[2]));else{start=Number(match[1]);if(match[2])end=Math.min(Number(match[2]),end);}
  if(start>end||start<0||start>=file.size)throw new ApiError(416,'Invalid media range.');status=206;headers.set('Content-Range',`bytes ${start}-${end}/${file.size}`);
 }
 headers.set('Content-Length',String(end-start+1));
 return new Response(Readable.toWeb(createReadStream(file.path,{start,end})) as ReadableStream,{status,headers});
}
