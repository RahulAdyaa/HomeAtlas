import {locationLink,locationSentence} from './locations';
type Source={id:string;title?:string;locationId?:string;locationPath?:string};
type Bookmark={citations?:Record<string,unknown>[];[key:string]:unknown};
// Saved evidence is historical, but its navigation must use the source's current recorded location.
export function refreshSavedLocations<T extends Bookmark>(bookmarks:T[],sources:Source[],householdId:string):T[]{
 const byId=new Map(sources.map(source=>[source.id,source]));
 return bookmarks.map(bookmark=>({...bookmark,citations:(bookmark.citations||[]).map(citation=>{
  const source=byId.get(String(citation.sourceId));
  const {locationUrl:oldUrl,locationDescription:oldDescription,locationId:oldId,locationPath:oldPath,sourceRemoved:oldRemoved,...evidence}=citation;
  if(!source?.locationId)return {...evidence,sourceRemoved:true};
  return {...evidence,locationId:source.locationId,locationPath:source.locationPath,locationUrl:locationLink(householdId,source.locationId),locationDescription:locationSentence(source.title||String(citation.title||'Record'),source.locationPath||'')};
 })}));
}
