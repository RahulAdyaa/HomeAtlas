import {normalizeRecordName,recordNameSql} from './record-names';
import type {DB} from './db';
import {locationLink,locationSentence} from './locations';
export type LocationMatch={kind:'item'|'source';id:string;name:string;locationId:string;locationPath:string;locationUrl:string;locationDescription:string;photoSourceId?:string|null;recordRemoved?:boolean};

export function locationTarget(question:string):string|null{
 const text=question.trim().replace(/[?!.]+$/,'');
 const match=text.match(/^(?:where\s+(?:is|are|can\s+i\s+find|did\s+i\s+(?:put|keep|store)|have\s+i\s+(?:put|kept|stored))|(?:please\s+)?(?:find|locate))\s+(.+)$/i)
  ??text.match(/^(.*?)\s+(?:kahan|kahaan|kaha|kidhar)\s+(?:hai|hain)$/i);
 if(!match)return null;
 const target=match[1].replace(/^(?:(?:my|our|the|a|an|mera|meri|mere)\s+)+/i,'').replace(/\s+(?:located|stored|kept)$/i,'').trim();
 return target?target:null;
}
export function includeDemo(question:string){return /\b(sample|demo|demonstration|example)\b/i.test(question)}
export function recordLocation(householdId:string,kind:'item'|'source',row:{id:string;name?:string;title?:string;location_id?:string;locationId?:string;location_path?:string;locationPath?:string;photo_source_id?:string|null;photoSourceId?:string|null}):LocationMatch{
 const name=row.name||row.title||'Record',locationId=row.location_id||row.locationId!,locationPath=row.location_path||row.locationPath||'';
 return {kind,id:row.id,name,locationId,locationPath,locationUrl:locationLink(householdId,locationId),locationDescription:locationSentence(name,locationPath),photoSourceId:row.photo_source_id||row.photoSourceId||null};
}
export function locationReply(matches:LocationMatch[]){
 const paths=new Set(matches.map(m=>m.locationId));
 const answer=matches.length===1?`${matches[0].name} is recorded in ${matches[0].locationPath.split(' > ').join(' → ')}.`:
 `${paths.size>1?'I found more than one recorded location; choose the matching record.':'I found these matching records:'}\n\n${matches.map(m=>`- ${m.name}: ${m.locationPath.split(' > ').join(' → ')}`).join('\n')}`;
 return {answer,confidence:paths.size>1?'conflicting':'supported',mode:'recorded-location',citations:[],locationMatches:matches};
}
export async function lookupLocation(db:DB,householdId:string,question:string,itemId?:string|null,roomId?:string|null){
 const target=locationTarget(question);if(!target)return null;
 const normalized=normalizeRecordName(target),demo=includeDemo(question);if(!normalized)return null;
 const items=(await db.query(`SELECT id,name,location_id,location_path,photo_source_id FROM items
 WHERE household_id=$1 AND ($2::uuid IS NULL OR id=$2) AND ($4::uuid IS NULL OR room_id=$4)
 AND (${recordNameSql('name')}=$3 OR ($2::uuid IS NOT NULL AND $3 IN ('it','thisitem','this')))
 ORDER BY created_at,id LIMIT 30`,[householdId,itemId||null,normalized,roomId||null])).rows;
 // Title matching works even before OCR finishes. This answers the recorded location, not document contents.
 const sources=(await db.query(`SELECT s.id,s.title,s.location_id,s.location_path,s.photo_source_id FROM sources s
 WHERE s.household_id=$1 AND ($2::uuid IS NULL OR s.item_id=$2) AND ($4::uuid IS NULL OR s.room_id=$4)
 AND ${recordNameSql("regexp_replace(s.title,'\\.[A-Za-z0-9]{1,12}$','','g')")}=$3
 AND ($5::boolean OR (s.title !~* '^SAMPLE[[:space:]—:-]' AND NOT EXISTS(SELECT 1 FROM chunks c WHERE c.source_id=s.id AND c.household_id=s.household_id AND c.metadata->>'sample'='true')))
 ORDER BY s.created_at,s.id LIMIT 30`,[householdId,itemId||null,normalized,roomId||null,demo])).rows;
 const matches=[...items.map(r=>recordLocation(householdId,'item',r)),...sources.map(r=>recordLocation(householdId,'source',r))];
 return matches.length?locationReply(matches):null;
}
