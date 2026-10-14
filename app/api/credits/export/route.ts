import { api,scope } from '@/lib/server';
import { pool } from '@/lib/db';
export const runtime='nodejs';
function csv(value:unknown){const text=String(value??'');return `"${(/^[=+\-@\t\r]/.test(text)?"'":'')+text.replace(/"/g,'""')}"`;}
export const GET=api(async(request)=>{
 const context=await scope(request);
 const{rows}=await pool.query('SELECT created_at,operation_id,kind,amount,available_delta,reserved_delta,description,actor_id FROM credit_ledger WHERE household_id=$1 ORDER BY created_at,id',[context.householdId]);
 const columns=['created_at','operation_id','kind','amount','available_delta','reserved_delta','description','actor_id'];
 const content=[columns.join(','),...rows.map(row=>columns.map(key=>csv(row[key] instanceof Date?row[key].toISOString():row[key])).join(','))].join('\r\n');
 return new Response(content,{headers:{'Content-Type':'text/csv; charset=utf-8','Content-Disposition':'attachment; filename="homeatlas-credits.csv"'}});
});
