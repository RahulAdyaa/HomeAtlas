'use client';
import type {CSSProperties,HTMLAttributes} from 'react';
/** Original implementation of the perspective-card pattern researched on 21st.dev.
 * No per-pointer React renders. Keyboard/touch need no motion to operate the contents. */
export default function DepthCard({children,className='',...props}:HTMLAttributes<HTMLDivElement>){
 return <div {...props} className={'depth-card '+className} style={{'--tilt-x':'0deg','--tilt-y':'0deg',...props.style} as CSSProperties} onPointerMove={event=>{
  if(event.pointerType!=='mouse'||window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const el=event.currentTarget,rect=el.getBoundingClientRect();
  el.style.setProperty('--tilt-x',`${-(event.clientY-rect.top-rect.height/2)/rect.height*5}deg`);
  el.style.setProperty('--tilt-y',`${(event.clientX-rect.left-rect.width/2)/rect.width*5}deg`);
 }} onPointerLeave={event=>{event.currentTarget.style.setProperty('--tilt-x','0deg');event.currentTarget.style.setProperty('--tilt-y','0deg')}}>{children}</div>
}
