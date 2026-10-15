import {api,scope,requireRole,audit} from '@/lib/server';
import {pool} from '@/lib/db';
import {callWorker} from '@/lib/worker';
export const runtime='nodejs';
export const GET=api(async request=>{
 const context=await scope(request);requireRole(context,['owner']);
 return Response.json(await callWorker('/cache/metrics',{householdId:context.householdId,actorId:context.user.id},request.signal));
});
export const DELETE=api(async request=>{
 const context=await scope(request);requireRole(context,['owner']);
 const result=await callWorker('/cache/clear',{householdId:context.householdId,actorId:context.user.id},request.signal);
 await audit(pool,context.householdId,context.user.id,'Cleared answer cache');
 return Response.json(result);
});
