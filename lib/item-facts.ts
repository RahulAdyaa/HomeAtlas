import type {DB} from './db';
import {normalizeRecordName,recordNameSql} from './record-names';
import {recordLocation,lookupLocation} from './location-lookup';
const fields=[
 {column:'serial_number',key:'serialNumber',label:'Serial number',aliases:['serial number','serial no','serial','identification number','id number','card number','aadhaar number','aadhar number','number']},
 {column:'model',key:'model',label:'Model',aliases:['model number','model']},
 {column:'make',key:'make',label:'Brand / make',aliases:['brand name','manufacturer','brand','make']},
 {column:'purchase_date',key:'purchaseDate',label:'Purchase date',aliases:['purchase date','purchased date','date of purchase']},
 {column:'warranty_date',key:'warrantyDate',label:'Warranty end date',aliases:['warranty expiration date','warranty expiry date','warranty end date','warranty date','warranty ends','warranty expires']},
 {column:'category',key:'category',label:'Category',aliases:['category']},
 {column:'notes',key:'notes',label:'Notes',aliases:['notes']},
] as const;
export type ItemFactIntent={target:string;field:typeof fields[number]};
export function itemFactIntent(question:string):ItemFactIntent|null{
 let body=question.trim().replace(/[?!.]+$/,'').replace(/[’‘]/g,"'");
 const clean=(target:string)=>target.replace(/^(?:(?:my|our|the|a|an)(?:\s+|$))+/i,'').replace(/'s$/i,'').trim();
 const warranty=body.match(/^when\s+(?:does|will)\s+(.+?)\s+warranty\s+(?:expire|end)$/i);
 if(warranty&&clean(warranty[1]))return {target:clean(warranty[1]),field:fields.find(f=>f.key==='warrantyDate')!};
 const purchase=body.match(/^when\s+did\s+i\s+(?:buy|purchase)\s+(.+)$/i)||body.match(/^when\s+was\s+(.+?)\s+(?:bought|purchased)$/i);
 if(purchase&&clean(purchase[1]))return {target:clean(purchase[1]),field:fields.find(f=>f.key==='purchaseDate')!};
 const request=body.match(/^(?:what(?:'s|\s+(?:is|are))|(?:please\s+)?(?:tell|show|give)(?:\s+me)?)\s+(.+)$/i);
 if(!request)return null;body=request[1];
 // Match longest phrases first: "model number" must not become generic "number".
 const aliases=fields.flatMap(field=>field.aliases.map(alias=>({field,alias}))).sort((a,b)=>b.alias.length-a.alias.length);
 for(const {field,alias} of aliases){
  const found=new RegExp(`\\b${alias}\\b`,'i').exec(body);if(!found)continue;
  const before=body.slice(0,found.index).trim(),after=body.slice(found.index+found[0].length).trim();
  let target='';
  if(!after)target=before;
  else if(/^(?:of|for|on)\b/i.test(after)&&/^(?:(?:my|our|the|a|an)\s*)?$/i.test(before))target=after.replace(/^(?:of|for|on)\s+/i,'');
  else continue;
  target=clean(target);
  if(target&&normalizeRecordName(target))return {target,field};
 }
 return null;
}
export async function lookupItemFact(db:DB,householdId:string,question:string,itemId?:string|null,roomId?:string|null){
 const intent=itemFactIntent(question);if(!intent)return null;
 const {field,target}=intent;
 // The selected column comes exclusively from the server-owned field list, never generated SQL.
 const rows=(await db.query(`SELECT id,name,location_id,location_path,photo_source_id,${field.column} AS recorded_value FROM items
 WHERE household_id=$1 AND ($2::uuid IS NULL OR id=$2) AND ($4::uuid IS NULL OR room_id=$4)
 AND (${recordNameSql('name')}=$3 OR ($2::uuid IS NOT NULL AND $3 IN ('it','thisitem','this')))
 ORDER BY created_at,id LIMIT 6`,[householdId,itemId||null,normalizeRecordName(target),roomId||null])).rows;
 if(!rows.length||rows.every(row=>row.recorded_value===null||String(row.recorded_value).trim()===''))return null;
 const locations=rows.slice(0,5).map(row=>recordLocation(householdId,'item',row));
 if(rows.length>5||(rows.length>1&&rows.reduce((sum,row)=>sum+String(row.recorded_value??'').length,0)>12000))return {answer:`I found several matching inventory records for ${target}. Select the intended item before asking for its ${field.label.toLowerCase()}.`,confidence:'conflicting',mode:'recorded-fact',citations:[],locationMatches:locations,recordFacts:[]};
 const facts=rows.map(row=>({kind:'item' as const,id:row.id,name:row.name,field:field.key,label:field.label,value:row.recorded_value===null||String(row.recorded_value).trim()===''?null:String(row.recorded_value),locationPath:row.location_path}));
 const values=new Set(facts.map(f=>f.value));
 const answer=facts.length===1?`${facts[0].name} — ${field.label}: ${facts[0].value}`:
 `I found multiple matching inventory records${values.size>1?' with different recorded values':''}:\n\n${facts.map(f=>`- ${f.name} (${f.locationPath}) — ${field.label}: ${f.value??'Not recorded'}`).join('\n')}`;
 return {answer,confidence:values.size>1?'conflicting':'supported',mode:'recorded-fact',citations:[],locationMatches:locations,recordFacts:facts};
}
export async function lookupSavedRecord(db:DB,householdId:string,question:string,itemId?:string|null,roomId?:string|null){
 return await lookupLocation(db,householdId,question,itemId,roomId)??await lookupItemFact(db,householdId,question,itemId,roomId);
}
