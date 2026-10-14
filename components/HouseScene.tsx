'use client';
import {Canvas,useFrame,useThree} from '@react-three/fiber';
import {Html,OrbitControls,OrthographicCamera,RoundedBox} from '@react-three/drei';
import {Component,createContext,useContext,useEffect,useMemo,useRef,useState,type ReactNode,type RefObject} from 'react';
import {Vector3, type MeshStandardMaterial} from 'three';
import type {OrbitControls as Controls} from 'three-stdlib';
import {ancestry,descendants,type LocationNode} from '@/lib/locations';
import type {RecordRow} from './types';
import styles from './HomeSpace.module.css';
type Props={locations:LocationNode[];sources:RecordRow[];items:RecordRow[];selected?:string;roomId?:string;onSelect:(id:string)=>void};
const LabelPortal=createContext<RefObject<HTMLElement>|undefined>(undefined);
function Block({p,s,c,glow=false}:{p:[number,number,number];s:[number,number,number];c:string;glow?:boolean}){
 const material=useRef<MeshStandardMaterial>(null);const {invalidate}=useThree();const started=useRef(0);
 useEffect(()=>{started.current=performance.now();invalidate()},[glow,invalidate]);
 useFrame(()=>{if(!material.current)return;const elapsed=performance.now()-started.current;material.current.emissiveIntensity=glow?.25+(elapsed<4000?Math.sin(elapsed/220)*.2:0):0;if(glow&&elapsed<4000)invalidate()});
 return <RoundedBox args={s} radius={Math.min(.05,...s.map(v=>v/4))} smoothness={2} position={p} castShadow receiveShadow><meshStandardMaterial ref={material} color={c} roughness={.85} emissive={glow?'#4865df':'#000000'}/></RoundedBox>
}
// Presets are normalized furniture; saved node dimensions and transforms set their actual size.
function Furniture({node,selected}:{node:LocationNode;selected:boolean}){
 const c=node.color,k=node.preset;
 const block=(p:[number,number,number],s:[number,number,number],color=c)=><Block p={p} s={s} c={color} glow={selected}/>;
 return <group scale={[node.size.x,node.size.y,node.size.z]}>
 {['desk','table','counter'].includes(k)?<>{block([0,.9,0],[1,.14,1])}{[-.4,.4].flatMap(x=>[-.4,.4].map(z=><Block key={x+':'+z} p={[x,.43,z]} s={[.08,.86,.08]} c="#9b8f81"/>))}{k==='desk'&&block([0,1.14,-.3],[.42,.35,.06],'#5b6880')}</>:
 k==='bed'?<>{block([0,.3,0],[1,.6,1])}{block([0,.65,.1],[.98,.15,.75],'#f8fafc')}{block([0,.76,-.32],[.7,.16,.24],'#ffffff')}</>:
 ['sofa','chair'].includes(k)?<>{block([0,.35,0],[1,.7,1])}{block([0,.8,-.4],[1,.4,.18])}{block([-.45,.65,0],[.1,.3,1])}{block([.45,.65,0],[.1,.3,1])}</>:
 ['storage','washroom','area'].includes(k)?<>{block([0,.04,0],[1,.08,1])}{node.attached&&<><Block p={[0,.5,-.49]} s={[1,1,.03]} c="#f4f5f7"/><Block p={[-.49,.5,0]} s={[.03,1,1]} c="#f4f5f7"/><Block p={[.49,.5,0]} s={[.03,1,1]} c="#f4f5f7"/><Block p={[-.35,.5,.49]} s={[.3,1,.03]} c="#f4f5f7"/><Block p={[.35,.5,.49]} s={[.3,1,.03]} c="#f4f5f7"/><Block p={[0,.94,.49]} s={[.4,.12,.03]} c="#f4f5f7"/></>}</>:
 k==='toilet'?<>{block([0,.3,.1],[.7,.6,.7],'#ffffff')}{block([0,.7,-.32],[.75,.6,.3],'#ffffff')}</>:
 k==='sink'?<>{block([0,.45,0],[.8,.9,.8])}{block([0,.94,0],[1,.12,1],'#ffffff')}{block([0,1.02,0],[.65,.05,.65],'#d5e5ee')}</>:
 k==='window'?<>{block([0,.5,0],[1,1,.1],'#b7ddea')}{block([0,.5,.06],[.04,1,.02],'#ffffff')}</>:
 k==='door'?block([0,.5,0],[1,1,.08],'#dec9ac'):
 <>{block([0,.5,0],[1,1,1])}{k==='washer'?<mesh position={[0,.5,.505]} rotation={[Math.PI/2,0,0]}><cylinderGeometry args={[.3,.3,.02,20]}/><meshStandardMaterial color="#8198ab"/></mesh>:block([0,.6,.505],[.04,.16,.025],'#ffffff')}</>}
 </group>
}
function Walls({node,cut=false}:{node:LocationNode;cut?:boolean}){
 const {x:w,z:d,y:h}=node.size;
 return <>{(['north','south','east','west'] as const).map(wall=>{
 const horizontal=wall==='north'||wall==='south',length=horizontal?w:d;
 const openings=(node.openings||[]).filter(o=>o.wall===wall).map(o=>({...o,start:Math.max(-length/2,o.offset*length-length/2-o.width/2),end:Math.min(length/2,o.offset*length-length/2+o.width/2)})).sort((a,b)=>a.start-b.start);
 const parts:ReactNode[]=[];const wallHeight=cut||wall==='south'||wall==='east'?.22:h;
 const piece=(a:number,b:number,bottom:number,top:number,color='#f7f8fb')=>{if(b<=a||top<=bottom)return;parts.push(<Block key={parts.length} p={horizontal?[(a+b)/2,(top+bottom)/2,wall==='north'?-d/2:d/2]:[wall==='west'?-w/2:w/2,(top+bottom)/2,(a+b)/2]} s={horizontal?[b-a,top-bottom,.09]:[.09,top-bottom,b-a]} c={color}/>)};
 let cursor=-length/2;for(const o of openings){piece(cursor,o.start,0,wallHeight);if(o.kind==='window'){piece(o.start,o.end,0,Math.min(.8,wallHeight));if(wallHeight>.8)piece(o.start,o.end,.8,Math.min(1.8,wallHeight),'#c2e1ed')}piece(o.start,o.end,o.kind==='door'?2:1.8,wallHeight);cursor=Math.max(cursor,o.end)}piece(cursor,length/2,0,wallHeight);return <group key={wall}>{parts}</group>;
 })}</>
}
function Label({node,count,itemCount=0,priority=0,onSelect}:{node:LocationNode;count:number;itemCount?:number;priority?:number;onSelect:()=>void}){return <Html portal={useContext(LabelPortal)} center position={[0,node.type==='room'?.25:node.size.y+.3,node.type==='room'?node.size.z*.25:0]} zIndexRange={[40,0]}><button data-home-label data-priority={priority} className={styles.label} title={`${node.name} · ${count} documents`} onClick={e=>{e.stopPropagation();onSelect()}}>{node.name}<small>{count} documents{itemCount?` · ${itemCount} items`:null}</small></button></Html>}
function LabelCollisions(){const portal=useContext(LabelPortal);const {gl}=useThree();useFrame(()=>{
 const root=portal?.current||gl.domElement.parentElement;if(!root)return;const bounds=root.getBoundingClientRect();const occupied:DOMRect[]=[];
 Array.from(root.querySelectorAll<HTMLElement>('[data-home-label]')).sort((a,b)=>Number(b.dataset.priority)-Number(a.dataset.priority)).forEach(el=>{const rect=el.getBoundingClientRect();const visible=rect.left>=bounds.left&&rect.right<=bounds.right&&rect.top>=bounds.top&&rect.bottom<=bounds.bottom&&!occupied.some(r=>rect.left<r.right+8&&rect.right>r.left-8&&rect.top<r.bottom+8&&rect.bottom>r.top-8);el.style.visibility=visible?'visible':'hidden';el.style.pointerEvents=visible?'auto':'none';if(visible)occupied.push(rect)});
 });return null}
function Camera({locations,roomId,reset}:{locations:LocationNode[];roomId?:string;reset:number}){
 const controls=useRef<Controls>(null);const {camera,size,invalidate}=useThree();const motion=useRef<{start:number;from:Vector3;to:Vector3;targetFrom:Vector3;targetTo:Vector3;zoomFrom:number;zoomTo:number}|null>(null);
 const rooms=locations.filter(n=>n.type==='room');const focus=rooms.find(n=>n.id===roomId);
 const bounds=useMemo(()=>{if(!rooms.length)return {x:0,z:0,w:12,d:12};const minX=Math.min(...rooms.map(n=>n.position.x-n.size.x/2)),maxX=Math.max(...rooms.map(n=>n.position.x+n.size.x/2)),minZ=Math.min(...rooms.map(n=>n.position.z-n.size.z/2)),maxZ=Math.max(...rooms.map(n=>n.position.z+n.size.z/2));return{x:(minX+maxX)/2,z:(minZ+maxZ)/2,w:maxX-minX,d:maxZ-minZ}},[locations]);
 useEffect(()=>{if(!controls.current)return;const x=focus?.position.x??bounds.x,z=focus?.position.z??bounds.z;const span=Math.max(focus?.size.x??bounds.w,focus?.size.z??bounds.d,4);motion.current={start:performance.now(),from:camera.position.clone(),to:new Vector3(x+12,15,z+14),targetFrom:controls.current.target.clone(),targetTo:new Vector3(x,0,z),zoomFrom:camera.zoom,zoomTo:Math.min(size.width/(span*1.65),size.height/(span*1.2))};invalidate()},[roomId,reset,bounds,size.width,size.height,camera,invalidate]);
 useFrame(()=>{const m=motion.current;if(!m||!controls.current)return;const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;const t=reduced?1:Math.min(1,(performance.now()-m.start)/800),ease=t*t*(3-2*t);camera.position.lerpVectors(m.from,m.to,ease);controls.current.target.lerpVectors(m.targetFrom,m.targetTo,ease);camera.zoom=m.zoomFrom+(m.zoomTo-m.zoomFrom)*ease;camera.updateProjectionMatrix();controls.current.update();if(t===1)motion.current=null;else invalidate()});
 return <OrbitControls ref={controls} makeDefault enableDamping minPolarAngle={.2} maxPolarAngle={1.25} minZoom={8} maxZoom={180} onStart={()=>{motion.current=null}}/>
}
class Boundary extends Component<{children:ReactNode;fallback:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return{failed:true}}render(){return this.state.failed?this.props.fallback:this.props.children}}
export default function HouseScene({locations,sources,items,selected,roomId,onSelect}:Props){
 const portal=useRef<HTMLDivElement>(null!);
 const [webgl,setWebgl]=useState<boolean|null>(null),[reset,setReset]=useState(0),[hover,setHover]=useState('');
 useEffect(()=>{try{const canvas=document.createElement('canvas'),context=canvas.getContext('webgl2');setWebgl(!!context);context?.getExtension('WEBGL_lose_context')?.loseContext()}catch{setWebgl(false)}},[]);
 const count=(id:string)=>{const ids=descendants(locations,id);return sources.filter(s=>ids.has(s.locationId||s.roomId)).length};
 const path=selected?ancestry(locations,selected):[];
 const fallback=<div className={styles.fallback}><p>Room list · all locations remain available without 3D.</p>{locations.filter(n=>n.type!=='home').map(n=><button key={n.id} onClick={()=>onSelect(n.id)}>{ancestry(locations,n.id).filter(a=>a.type!=='home').map(a=>a.name).join(' › ')} · {count(n.id)} documents</button>)}</div>;
 if(webgl===null)return <div className={styles.canvas}>Preparing your home…</div>;if(!webgl)return fallback;
 return <Boundary fallback={fallback}><div className={styles.scene}><div className={styles.canvas} aria-label="Interactive 3D home"><div ref={portal} style={{position:'absolute',inset:0,pointerEvents:'none',zIndex:2}}/><LabelPortal.Provider value={portal}><Canvas shadows frameloop="demand" dpr={[1,1.5]} gl={{antialias:true}} onCreated={({gl})=>gl.domElement.addEventListener('webglcontextlost',()=>setWebgl(false),{once:true})}><color attach="background" args={['#f1f4f9']}/><OrthographicCamera makeDefault position={[18,18,20]} zoom={35}/><ambientLight intensity={1.5}/><directionalLight position={[5,16,8]} intensity={2} castShadow shadow-mapSize={[1024,1024]} shadow-camera-left={-30} shadow-camera-right={30} shadow-camera-top={30} shadow-camera-bottom={-30}/>{locations.filter(n=>n.type==='room'&&(!roomId||n.id===roomId)).map(room=><group key={room.id} position={[room.position.x,room.position.y,room.position.z]} rotation={[0,room.rotation*Math.PI/180,0]} onClick={e=>{e.stopPropagation();onSelect(room.id)}} onPointerOver={e=>{e.stopPropagation();setHover(room.id)}} onPointerOut={()=>setHover('')}><Block p={[0,-.12,0]} s={[room.size.x,.24,room.size.z]} c={hover===room.id?'#d3ddf7':room.color} glow={path.some(n=>n.id===room.id)}/><Walls node={room} cut={!!roomId}/>{locations.filter(n=>n.parentId===room.id).map(zone=><group key={zone.id} position={[zone.position.x,zone.position.y,zone.position.z]} rotation={[0,zone.rotation*Math.PI/180,0]} onClick={e=>{e.stopPropagation();onSelect(zone.id)}}><Furniture node={zone} selected={path.some(n=>n.id===zone.id)}/>{roomId&&locations.filter(n=>n.parentId===zone.id).map(container=><group key={container.id} position={[container.position.x,container.position.y,container.position.z]} rotation={[0,container.rotation*Math.PI/180,0]} onClick={e=>{e.stopPropagation();onSelect(container.id)}}><Block p={[0,container.size.y/2,0]} s={[container.size.x,container.size.y,container.size.z]} c={container.color} glow={selected===container.id}/>{selected===container.id&&<Label node={container} priority={2} count={count(container.id)} onSelect={()=>onSelect(container.id)}/>}</group>)}{roomId&&<Label node={zone} count={count(zone.id)} itemCount={items.filter(i=>descendants(locations,zone.id).has(i.locationId)).length} onSelect={()=>onSelect(zone.id)}/>}</group>)}{!roomId&&<Label node={room} count={count(room.id)} onSelect={()=>onSelect(room.id)}/>}</group>)}<Camera locations={locations} roomId={roomId} reset={reset}/><LabelCollisions/></Canvas></LabelPortal.Provider></div><div className={styles.sceneTools}><span aria-live="polite">{hover?`${locations.find(n=>n.id===hover)?.name} · ${count(hover)} documents`:'Drag to orbit · pinch or scroll to zoom'}</span><button onClick={()=>setReset(r=>r+1)}>Reset view</button></div></div></Boundary>
}
