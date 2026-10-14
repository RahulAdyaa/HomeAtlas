import { getMigrations } from 'better-auth/db/migration';
import { readFile } from 'node:fs/promises';
import { auth } from '../lib/auth';
import { pool } from '../lib/db';
async function main(){
 const {runMigrations}=await getMigrations(auth.options);
 await runMigrations();
 const db=await pool.connect();
 try {for(const file of ['001_core.sql','002_locations.sql','003_location_photos.sql']) {
  const sql=await readFile(new URL('../db/'+file,import.meta.url),'utf8');
  await db.query('BEGIN');
  try {await db.query(sql);await db.query('COMMIT');} catch(error){await db.query('ROLLBACK');throw error;}
 }} finally {db.release();}
 console.log('HomeAtlas database and Better Auth migrations applied.');
 await pool.end();
}
main().catch(error=>{console.error(error);process.exitCode=1;pool.end();});
