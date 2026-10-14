import {beforeAll,afterAll,it,expect} from 'vitest';
import {randomUUID} from 'node:crypto';
let pool:typeof import('../lib/db').pool,route:typeof import('../app/api/locations/route'),cookie='',actor='';
const home=randomUUID(),other=randomUUID(),origin='http://localhost:3000';
const request=(body:object)=>new Request(origin+'/api/locations?householdId='+home,{method:'POST',headers:{origin,cookie,'content-type':'application/json'},body:JSON.stringify(body)});
beforeAll(async()=>{
 process.env.BETTER_AUTH_SECRET??='location-test-secret-at-least-32-characters';process.env.BETTER_AUTH_URL=origin;
 ({pool}=await import('../lib/db'));route=await import('../app/api/locations/route');const {auth}=await import('../lib/auth');
 const email=randomUUID()+'@example.invalid',password='Fixture-'+randomUUID();actor=(await auth.api.signUpEmail({body:{name:'Location fixture',email,password}})).user.id;
 await pool.query('UPDATE "user" SET "emailVerified"=true WHERE id=$1',[actor]);cookie=(await auth.api.signInEmail({body:{email,password},asResponse:true})).headers.getSetCookie().map(c=>c.split(';')[0]).join('; ');
 for(const id of [home,other])await pool.query('INSERT INTO households(id,name,created_by) VALUES($1,$2,$3)',[id,'Fixture home',actor]);
 await pool.query("INSERT INTO memberships(household_id,user_id,role) VALUES($1,$2,'owner')",[home,actor]);
});
afterAll(async()=>{await pool.query('DELETE FROM households WHERE id=ANY($1::uuid[])',[[home,other]]);await pool.query('DELETE FROM "user" WHERE id=$1',[actor]);await pool.end()});
it('creates room/zone/container, moves documents, updates paths, and blocks invalid edits',async()=>{
 const create=async(parentId:string,type:string,name:string)=>{const res=await route.POST(request({action:'create',parentId,type,name}));expect(res.status).toBe(200);return(await res.json()).id};
 const room=await create(home,'room','Study'),zone=await create(room,'zone','Desk'),container=await create(zone,'container','Top drawer');
 expect((await route.POST(request({action:'create',parentId:other,type:'room',name:'Not yours'}))).status).toBe(404);
 expect((await route.POST(request({action:'create',parentId:room,type:'container',name:'Bad parent'}))).status).toBe(400);
 const source=randomUUID();await pool.query("INSERT INTO sources(id,household_id,room_id,title,mime_type,created_by) VALUES($1,$2,$3,'Demo.txt','text/plain',$4)",[source,home,room,actor]);
 expect((await route.POST(request({action:'attach',id:source,kind:'source',locationId:container}))).status).toBe(200);
 expect((await pool.query('SELECT location_path FROM sources WHERE id=$1',[source])).rows[0].location_path).toBe('Study > Desk > Top drawer');
 expect((await route.POST(request({action:'delete',id:container}))).status).toBe(409);
 expect((await route.POST(request({action:'deleteSource',id:source}))).status).toBe(200);
 expect((await route.POST(request({action:'delete',id:container}))).status).toBe(200);
 await pool.query("UPDATE memberships SET role='viewer' WHERE household_id=$1 AND user_id=$2",[home,actor]);
 expect((await route.POST(request({action:'delete',id:zone}))).status).toBe(403);
});
