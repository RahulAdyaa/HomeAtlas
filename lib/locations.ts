export type Vector={x:number;y:number;z:number};
export type Opening={wall:'north'|'south'|'east'|'west';kind:'door'|'window';offset:number;width:number};
export type LocationNode={id:string;householdId:string;parentId:string|null;name:string;type:'home'|'room'|'zone'|'container';preset:string;position:Vector;size:Vector;rotation:number;icon:string;color:string;attached:boolean;openings:Opening[]};
export const presets=['area','bed','sofa','table','chair','desk','wardrobe','cabinet','tv','counter','fridge','washer','toilet','sink','window','door','storage','washroom','drawer','shelf','box'] as const;
export function ancestry(nodes:LocationNode[],id:string):LocationNode[]{const seen=new Set<string>(),path:LocationNode[]=[];let node=nodes.find(n=>n.id===id);while(node){if(seen.has(node.id))throw new Error('Location cycle');seen.add(node.id);path.unshift(node);node=nodes.find(n=>n.id===node!.parentId)}return path}
export function locationPath(nodes:LocationNode[],id:string){const path=ancestry(nodes,id);return path.filter(n=>n.type!=='home').map(n=>n.name).join(' > ')||path[0]?.name||''}
export function locationLink(householdId:string,locationId:string){return `/?householdId=${encodeURIComponent(householdId)}&location=${encodeURIComponent(locationId)}`}
export function descendants(nodes:LocationNode[],id:string):Set<string>{const result=new Set([id]);for(let i=0;i<4;i++)for(const node of nodes)if(node.parentId&&result.has(node.parentId))result.add(node.id);return result}
export function locationSentence(title:string,path:string){return `${title} is recorded at ${path.split(' > ').join(' → ')}.`}
