import { pool } from '@/lib/db';
import { workerHealth } from '@/lib/worker';
export const runtime='nodejs';
export async function GET(){
 let database='ok';try{await pool.query('SELECT 1');}catch{database='unavailable';}
 const worker=await workerHealth();const healthy=database==='ok'&&worker.status==='ok';
 return Response.json({status:healthy?'ok':'degraded',database,worker:worker.status,inference:'self-hosted'},{status:healthy?200:503,headers:{'Cache-Control':'no-store'}});
}
