import {Children, cloneElement, isValidElement, type ReactNode} from 'react';
import aliases from '@/config/search-aliases.json';

const STOP=new Set('a an the and or of in on to for my me our is are was were what which where when who how does do can you this that it with from about tell show please find give have did'.split(' '));
const WORD=/[\p{L}\p{N}]+/gu;
const groups=Object.entries(aliases).map(([key,values])=>[key,...values].map(v=>v.toLocaleLowerCase()));

function canonical(word:string){const lower=word.toLocaleLowerCase();return groups.find(group=>group.includes(lower))?.[0]||lower}
function distance(a:string,b:string){
  const row=Array.from({length:b.length+1},(_,i)=>i);
  for(let i=1;i<=a.length;i++){let prior=row[0];row[0]=i;for(let j=1;j<=b.length;j++){const old=row[j];row[j]=Math.min(row[j]+1,row[j-1]+1,prior+(a[i-1]===b[j-1]?0:1));prior=old}}
  return row[b.length];
}
export function highlightTerms(query:string,text:string){
  const terms=[...new Set((query.toLocaleLowerCase().match(WORD)||[]).filter(w=>w.length>2&&!STOP.has(w)))].slice(0,10);
  if(!terms.length)return [];
  return [...new Set(text.match(WORD)||[])].filter(word=>terms.some(term=>{
    const target=canonical(term),value=canonical(word);
    return target===value||(target.length>=5&&value.length>=5&&Math.abs(target.length-value.length)<=1&&distance(target,value)<=1);
  })).slice(0,30);
}

export function markedText(text:string,terms:string[]):ReactNode{
  if(!terms.length)return text;
  const escaped=terms.map(term=>term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).sort((a,b)=>b.length-a.length);
  const expression=new RegExp(`(?<![\\p{L}\\p{N}])(${escaped.join('|')})(?![\\p{L}\\p{N}])`,'giu');
  return text.split(expression).map((part,index)=>terms.some(term=>term.toLocaleLowerCase()===part.toLocaleLowerCase())?
    <mark key={index}>{part}</mark>:part);
}

export function highlightNodes(children:ReactNode,terms:string[],citation?:(number:number)=>ReactNode):ReactNode{
  return Children.map(children,child=>{
    if(typeof child==='string')return child.split(/(⟦\d+⟧)/g).map(part=>{
      const number=/^⟦(\d+)⟧$/.exec(part);
      return number&&citation?citation(Number(number[1])):markedText(part,terms);
    });
    if(!isValidElement<{children?:ReactNode;className?:string}>(child))return child;
    const type=typeof child.type==='string'?child.type:'';
    if(type==='code'||type==='pre'||child.props.className?.includes('katex'))return child;
    return cloneElement(child,{},highlightNodes(child.props.children,terms,citation));
  });
}
