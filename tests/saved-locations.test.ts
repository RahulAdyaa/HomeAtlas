import {it,expect} from 'vitest';
import {refreshSavedLocations} from '../lib/saved-locations';
it('refreshes historical answer navigation after a source moves without rewriting its evidence',()=>{
 const result=refreshSavedLocations([{answer:'Historical answer',citations:[{id:'chunk',sourceId:'s',title:'Receipt',text:'Original quotation',locationPath:'Old room',locationUrl:'https://untrusted.invalid'}]}],[{id:'s',title:'Receipt',locationId:'drawer',locationPath:'Study > Desk > Top drawer'}],'household');
 expect(result[0].citations[0]).toMatchObject({text:'Original quotation',locationPath:'Study > Desk > Top drawer',locationUrl:'/?householdId=household&location=drawer'});
 expect(result[0].answer).toBe('Historical answer');
});
it('removes stale navigation when the original source was deleted or is outside the scoped source list',()=>{
 const result=refreshSavedLocations([{citations:[{sourceId:'deleted',locationUrl:'/?location=old',locationDescription:'Old room'}]}],[],'h');
 expect(result[0].citations[0]).toEqual({sourceId:'deleted',sourceRemoved:true});
});
it('preserves search-only bookmarks without adding fake locations',()=>expect(refreshSavedLocations([{question:'Find my manual'}],[],'h')).toEqual([{question:'Find my manual',citations:[]}]));
