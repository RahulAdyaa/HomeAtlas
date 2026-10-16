import type {Citation} from './types';
import {highlightTerms,markedText} from '@/lib/answer-highlight';
import {readableSnippet} from '@/lib/evidence-display';

export default function SourceCards({citations,query,onOpen,scopedPath}:{citations:Citation[];query:string;onOpen:(citation:Citation)=>void;scopedPath:(path:string)=>string}){
 const documents=new Map<string,Citation[]>();
 for(const citation of citations){const key=`${citation.sourceId}:${citation.versionId}`;documents.set(key,[...(documents.get(key)||[]),citation])}
 if(!citations.length)return null;
 return <details className="source-cards"><summary>Evidence · {documents.size} {documents.size===1?'document':'documents'}</summary>
  {[...documents].map(([key,entries])=>{
   const primary=entries[0],pages=[...new Set(entries.map(c=>c.page).filter(Boolean))].sort((a,b)=>Number(a)-Number(b));
   return <section className="source-card" key={key} aria-label={`Source ${primary.title}`}>
    <div className="source-card-heading"><strong>{primary.title}</strong><span>{primary.locationPath||'Location not recorded'}</span></div>
    <p>{pages.length?`Pages ${pages.join(', ')}`:`${entries.length} cited passage${entries.length===1?'':'s'}`}</p>
    <div className="source-card-links">{primary.locationUrl&&<a href={primary.locationUrl}>Show location in 3D ↗</a>}
     <a href={scopedPath(`/api/sources/${primary.sourceId}?version=${primary.versionId}${pages[0]?`#page=${pages[0]}`:''}`)} target="_blank" rel="noopener noreferrer">Open original{pages[0]?` at page ${pages[0]}`:''} ↗</a></div>
    {entries.map(c=>{const snippet=readableSnippet(c.text),terms=highlightTerms(query,snippet);return <button type="button" className="evidence-snippet" key={c.id} onClick={()=>onOpen(c)} title={`Open ${c.title}${c.page?` page ${c.page}`:''}`}>
     <span className="citation-chip">{c.number||citations.indexOf(c)+1}</span><span>{markedText(snippet,terms)}</span>
    </button>})}
   </section>
  })}
 </details>;
}
