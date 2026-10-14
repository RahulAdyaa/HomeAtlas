import type {LocationNode,Vector} from './locations';
export const snap=(value:number)=>Math.round(value*4)/4;
export function presetSize(preset:string):Vector{
 const sizes:Record<string,[number,number,number]>={bed:[1.6,.65,2],sofa:[2.2,.8,.9],desk:[1.5,.8,.7],table:[1.2,.8,.8],chair:[.5,.8,.5],wardrobe:[1.5,1.9,.6],cabinet:[1,.9,.5],tv:[1.4,1,.3],counter:[2.5,.9,.6],fridge:[.7,1.7,.7],washer:[.65,.9,.65],toilet:[.5,.8,.7],sink:[.6,.85,.5],window:[1.2,1,.12],door:[.9,2,.12],storage:[1.5,2,1.5],washroom:[1.7,2,1.8],drawer:[.6,.2,.45],shelf:[.8,.15,.3],box:[.4,.3,.4]};const [x,y,z]=sizes[preset]||[1,.1,1];return{x,y,z};
}
export function emptyLocation(householdId:string,parentId:string,type:LocationNode['type'],preset='area'):LocationNode{return{id:crypto.randomUUID(),householdId,parentId,type,preset,name:type==='room'?'New room':preset[0].toUpperCase()+preset.slice(1),position:{x:0,y:0,z:0},size:type==='room'?{x:4,y:2.5,z:4}:presetSize(preset),rotation:0,color:type==='room'?'#dce7f6':'#c4d3e7',icon:'box',attached:['storage','washroom'].includes(preset),openings:[]}}
