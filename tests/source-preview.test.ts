import {beforeEach,describe,expect,it,vi} from 'vitest';
const mocks=vi.hoisted(()=>({query:vi.fn(),scope:vi.fn(),media:vi.fn()}));
vi.mock('../lib/server',async()=>{
 const {z}=await import('zod');
 return {api:(handler:unknown)=>handler,scope:mocks.scope,uuid:z.string().uuid(),ApiError:class extends Error{constructor(public status:number,message:string){super(message);}}};
});
vi.mock('../lib/db',()=>({pool:{query:mocks.query},camel:(value:unknown)=>value}));
vi.mock('../lib/media',()=>({privateMedia:mocks.media}));
import {GET} from '../app/api/sources/[id]/route';
const id='11111111-1111-4111-8111-111111111111',version='22222222-2222-4222-8222-222222222222';
const request=(query='preview=true&page=2')=>new Request(`http://localhost/api/sources/${id}?version=${version}&${query}`);
const params={params:Promise.resolve({id})};
beforeEach(()=>{vi.resetAllMocks();mocks.scope.mockResolvedValue({householdId:'household'});mocks.query.mockResolvedValueOnce({rows:[{id,version_id:version,title:'Manual',mime_type:'application/pdf'}]});mocks.media.mockResolvedValue(new Response('png'));});
describe('authenticated source page previews',()=>{
 it('reads the requested page from the authorized immutable version',async()=>{
  mocks.query.mockResolvedValueOnce({rows:[{image_path:'/private/page-2.png'}]});
  const response=await GET(request(),params);expect(await response.text()).toBe('png');
  expect(mocks.query.mock.calls[1][1]).toEqual(['household',id,version,2]);
  expect(mocks.media).toHaveBeenCalledWith(expect.any(Request),'/private/page-2.png','image/png','Manual page 2');
 });
 it('does not fall back to the original file when a page is unavailable',async()=>{
  mocks.query.mockResolvedValueOnce({rows:[]});
  await expect(GET(request(),params)).rejects.toMatchObject({status:404});expect(mocks.media).not.toHaveBeenCalled();
 });
 it('rejects invalid page numbers',async()=>{
  await expect(GET(request('preview=true&page=-1'),params)).rejects.toMatchObject({status:400});expect(mocks.media).not.toHaveBeenCalled();
 });
 it('requires household authorization before reading a source',async()=>{
  mocks.scope.mockRejectedValue(new Error('Unauthorized'));
  await expect(GET(request(),params)).rejects.toThrow('Unauthorized');expect(mocks.query).not.toHaveBeenCalled();
 });
});
