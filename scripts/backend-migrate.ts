import { getMigrations } from 'better-auth/db/migration';
import { readFile } from 'node:fs/promises';
import { auth } from '../lib/auth';
import { pool } from '../lib/db';
async function main(){
 const {runMigrations}=await getMigrations(auth.options);
 await runMigrations();
 const sql=await readFile(new URL('../db/001_core.sql',import.meta.url),'utf8');
 await pool.query(sql);
 console.log('HomeAtlas database and Better Auth migrations applied.');
 await pool.end();
}
main().catch(error=>{console.error(error);process.exitCode=1;pool.end();});
