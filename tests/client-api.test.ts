import {afterEach,expect,test,vi} from 'vitest';
import {requestJSON} from '../lib/client-api';
afterEach(()=>vi.unstubAllGlobals());
function transport(){const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({cleared:2})});vi.stubGlobal('fetch',fetch);return fetch;}
test('clear answer cache sends DELETE without a JSON method payload',async()=>{
 const fetch=transport();
 expect(await requestJSON('/api/cache?householdId=synthetic',undefined,'DELETE')).toEqual({cleared:2});
 expect(fetch).toHaveBeenCalledWith('/api/cache?householdId=synthetic',{method:'DELETE'});
});
test('ordinary reads, JSON writes and multipart uploads keep their transport',async()=>{
 const fetch=transport();
 await requestJSON('/api/atlas');await requestJSON('/api/action',{action:'rename'});
 const data=new FormData();data.set('title','Fictional manual');await requestJSON('/api/sources',data);
 expect(fetch.mock.calls[0][1]).toEqual({method:'GET'});
 expect(fetch.mock.calls[1][1]).toEqual({method:'POST',headers:{'Content-Type':'application/json'},body:'{"action":"rename"}'});
 expect(fetch.mock.calls[2][1]).toEqual({method:'POST',headers:{},body:data});
});
test('failed cache clear reports the actual API error',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,json:async()=>({error:'Household owner required'})}));
 await expect(requestJSON('/api/cache',undefined,'DELETE')).rejects.toThrow('Household owner required');
});
