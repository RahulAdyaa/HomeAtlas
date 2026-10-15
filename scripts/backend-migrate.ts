import { getMigrations } from 'better-auth/db/migration';
import { readFile } from 'node:fs/promises';
import { auth } from '../lib/auth';
import { pool } from '../lib/db';
async function main(){
 const {runMigrations}=await getMigrations(auth.options);
 await runMigrations();
 const db=await pool.connect();
 try {for(const file of ['001_core.sql','002_locations.sql','003_location_photos.sql','004_bookmark_locations.sql','005_hybrid_cache.sql']) {
  const sql=await readFile(new URL('../db/'+file,import.meta.url),'utf8');
  await db.query('BEGIN');
  try {await db.query(sql);await db.query('COMMIT');} catch(error){await db.query('ROLLBACK');throw error;}
 }
 const aliases=JSON.parse(await readFile(new URL('../config/search-aliases.json',import.meta.url),'utf8')) as Record<string,string[]>;
 await db.query('BEGIN');
 try {
  await db.query('DELETE FROM search_aliases');
  for(const [canonical,variants] of Object.entries(aliases))for(const alias of [canonical,...variants])await db.query('INSERT INTO search_aliases(alias,canonical) VALUES(atlas_search_basic($1),atlas_search_basic($2)) ON CONFLICT(alias) DO UPDATE SET canonical=excluded.canonical',[alias,canonical]);
  await db.query('UPDATE chunks SET text=text');
  await db.query('COMMIT');
 }catch(error){await db.query('ROLLBACK');throw error;}
 } finally {db.release();}
 console.log('HomeAtlas database and Better Auth migrations applied.');
 await pool.end();
}
main().catch(error=>{console.error(error);process.exitCode=1;pool.end();});
