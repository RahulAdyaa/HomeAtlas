'use client';
import {useState} from 'react';
import {ChevronLeft,ChevronRight} from 'lucide-react';
import type {RecordRow} from './types';
export default function MonthCalendar({tasks,onDate}:{tasks:RecordRow[];onDate:(date:string)=>void}){
 const [month,setMonth]=useState(()=>new Date(new Date().getFullYear(),new Date().getMonth(),1));
 const days=new Date(month.getFullYear(),month.getMonth()+1,0).getDate();const offset=(month.getDay()+6)%7;
 const key=(d:number)=>`${month.getFullYear()}-${String(month.getMonth()+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
 const today=new Date();const todayKey=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
 return <section className="card month-calendar"><div className="section-heading"><h2>{month.toLocaleDateString('en-GB',{month:'long',year:'numeric'})}</h2><div><button className="icon-button" aria-label="Previous month" onClick={()=>setMonth(new Date(month.getFullYear(),month.getMonth()-1,1))}><ChevronLeft size={17}/></button><button className="icon-button" aria-label="Next month" onClick={()=>setMonth(new Date(month.getFullYear(),month.getMonth()+1,1))}><ChevronRight size={17}/></button></div></div><div className="calendar-grid">{['M','T','W','T','F','S','S'].map((d,i)=><span className="weekday" key={i}>{d}</span>)}{Array.from({length:offset},(_,i)=><span key={'blank'+i}/>)}{Array.from({length:days},(_,i)=>{const d=i+1;const due=tasks.filter(t=>t.dueDate?.slice(0,10)===key(d)&&!t.completedAt);return <button key={d} className={(key(d)===todayKey?'today ':'')+(due.length?'has-task':'')} onClick={()=>onDate(key(d))} aria-label={`${month.toLocaleDateString('en-GB',{month:'long'})} ${d}${due.length?', '+due.map(t=>t.title).join(', '):', add reminder'}`}><span>{d}</span>{due.length>0&&<i/>}</button>})}</div><p><span className="green-dot"/> A small reminder. A little peace of mind.</p></section>
}
