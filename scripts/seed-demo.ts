import {pool,transaction} from '../lib/db';
import {seedDemoHome} from '../lib/demo-home';
import {removePrivateFile} from '../lib/storage';
const householdId=process.argv[2];
if(!householdId||! /^[0-9a-f-]{36}$/i.test(householdId))throw new Error('Usage: node --env-file=.env.local --import tsx scripts/seed-demo.ts HOUSEHOLD_UUID');
const files:string[]=[];
try{
 const result=await transaction(async db=>{
  const home=(await db.query('SELECT id FROM households WHERE id=$1 FOR UPDATE',[householdId])).rows[0];
  const owner=(await db.query("SELECT user_id FROM memberships WHERE household_id=$1 AND role='owner' ORDER BY created_at LIMIT 1",[householdId])).rows[0];
  if(!home||!owner)throw new Error('Home with owner not found.');
  return seedDemoHome(db,householdId,owner.user_id,files);
 });console.log(result.seeded?'Demo layout and four SAMPLE documents added.':'Demo already exists; no duplicate records added.');
}catch(error){await Promise.allSettled(files.map(removePrivateFile));throw error}finally{await pool.end()}
