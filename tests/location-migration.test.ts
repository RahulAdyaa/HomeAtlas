import {it,expect,afterAll} from 'vitest';
import {Pool} from 'pg';
import {randomUUID} from 'node:crypto';
import {readFile} from 'node:fs/promises';
const pool=new Pool({connectionString:process.env.DATABASE_URL||'postgres://homeatlas:homeatlas@127.0.0.1:54329/homeatlas'});
afterAll(()=>pool.end());
it('migrates legacy rooms idempotently, maintains paths and enforces household hierarchy',async()=>{
 const db=await pool.connect();await db.query('BEGIN');
 try{
  const actor=randomUUID(),h=randomUUID(),r=randomUUID(),z=randomUUID(),c=randomUUID(),s=randomUUID();
  await db.query(`INSERT INTO "user"(id,name,email,"emailVerified","createdAt","updatedAt") VALUES($1,'Fixture',$2,true,now(),now())`,[actor,actor+'@example.invalid']);
  await db.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3)',[h,'Fixture home',actor]);
  await db.query('INSERT INTO rooms(id,household_id,name,kind) VALUES($1,$2,$3,$4)',[r,h,'Study','study']);
  await db.query("INSERT INTO sources(id,household_id,room_id,title,mime_type,created_by) VALUES($1,$2,$3,'Fixture.txt','text/plain',$4)",[s,h,r,actor]);
  await db.query('SET CONSTRAINTS ALL IMMEDIATE');
  // Reapply the real migration to populated legacy-compatible fixtures.
  await db.query(await readFile(new URL('../db/002_locations.sql',import.meta.url),'utf8'));
  expect((await db.query('SELECT location_id,location_path,room_id FROM sources WHERE id=$1',[s])).rows[0]).toEqual({location_id:r,location_path:'Study',room_id:r});
  await db.query("INSERT INTO locations(id,household_id,parent_id,name,type) VALUES($1,$2,$3,'Desk','zone'),($4,$2,$1,'Top drawer','container')",[z,h,r,c]);
  await db.query('UPDATE sources SET location_id=$2 WHERE id=$1',[s,c]);
  expect((await db.query('SELECT location_path FROM sources WHERE id=$1',[s])).rows[0].location_path).toBe('Study > Desk > Top drawer');
  await db.query("UPDATE locations SET name='Writing desk' WHERE id=$1",[z]);
  expect((await db.query('SELECT location_path FROM sources WHERE id=$1',[s])).rows[0].location_path).toBe('Study > Writing desk > Top drawer');
  await db.query('SAVEPOINT invalid');
  await expect(db.query('UPDATE locations SET parent_id=$2 WHERE id=$1',[z,c])).rejects.toThrow('Invalid location parent');await db.query('ROLLBACK TO invalid');
  const other=randomUUID();await db.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3)',[other,'Other home',actor]);
  await db.query('SAVEPOINT tenant');await expect(db.query('UPDATE sources SET location_id=$2 WHERE id=$1',[s,other])).rejects.toThrow('Location outside household');await db.query('ROLLBACK TO tenant');
 }finally{await db.query('ROLLBACK');db.release()}
});
