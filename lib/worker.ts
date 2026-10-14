import { ApiError } from './server';
const workerUrl=process.env.WORKER_URL??'http://127.0.0.1:8001';
export async function callWorker(endpoint:string,body:Record<string,unknown>,signal?:AbortSignal){
 const key=process.env.WORKER_KEY;if(!key)throw new ApiError(503,'The private processing worker is not configured.');
 const timeout=AbortSignal.timeout(Math.min(300000,Number(process.env.WORKER_TIMEOUT_MS??300000)));
 let response:Response;
 try{response=await fetch(`${workerUrl}${endpoint}`,{method:'POST',headers:{'Content-Type':'application/json','X-Worker-Key':key},body:JSON.stringify(body),signal:signal?AbortSignal.any([signal,timeout]):timeout});}
 catch{throw new ApiError(503,'The private processing worker is unavailable or timed out. Your reserved credits will be returned.');}
 if(!response.ok){
  if(response.status===403)throw new ApiError(403,'Your household permission changed while processing this request.');
  if(response.status===422)throw new ApiError(422,'The worker could not process this media. Check its format and duration, and ensure the required local models are installed.');
  throw new ApiError(503,'The private processing worker could not complete this request. Your reserved credits will be returned.');
 }
 return response.json();
}
export async function workerHealth(){
 try {const response=await fetch(`${workerUrl}/health`,{signal:AbortSignal.timeout(3000)});if(!response.ok)return{status:'unavailable'};return await response.json();}catch{return{status:'unavailable'};}
}
