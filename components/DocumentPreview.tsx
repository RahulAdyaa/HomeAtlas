'use client';
import {useEffect,useState} from 'react';

type Chunk={id:string;page?:number;text:string};
export default function DocumentPreview({url,title,mime}:{url:string;title:string;mime?:string}){
 const [chunks,setChunks]=useState<Chunk[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[page,setPage]=useState(1),[imageFailed,setImageFailed]=useState(false);
 useEffect(()=>{
  const controller=new AbortController();
  setLoading(true);setError('');setChunks([]);setPage(1);setImageFailed(false);
  fetch(url+'&metadata=true',{signal:controller.signal}).then(async response=>{
   const data=await response.json();if(!response.ok)throw new Error(data.error||'Preview unavailable.');
   setChunks(data.chunks||[]);
  }).catch(reason=>{if(!controller.signal.aborted)setError(reason.message||'Preview unavailable.');})
   .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
  return()=>controller.abort();
 },[url]);
 if(loading)return <p className="citation-text-preview" role="status">Loading preview…</p>;
 if(error)return <p className="citation-text-preview" role="status">{error} You can still use Open original above.</p>;
 if(mime==='application/pdf'){
  const pages=[...new Set(chunks.map(chunk=>chunk.page).filter((value):value is number=>typeof value==='number'))].sort((a,b)=>a-b);
  const selected=pages.includes(page)?page:pages[0];
  if(!selected)return <p className="citation-text-preview">The page preview is not ready. Once processing finishes, reopen this record. You can also use Open original above.</p>;
  return <div className="citation-text-preview">
   <label className="field">Preview page<select aria-label="Preview page" value={selected} onChange={event=>{setPage(Number(event.target.value));setImageFailed(false);}}>{pages.map(number=><option key={number} value={number}>Page {number}</option>)}</select></label>
   {imageFailed?<p role="status">This page preview is unavailable. Use Open original above, or reprocess this record to rebuild its preview.</p>:<img src={url+`&preview=true&page=${selected}`} alt={`Page ${selected} of ${title}`} onError={()=>setImageFailed(true)}/>}
  </div>;
 }
 const text=chunks.filter(chunk=>chunk.text?.trim());
 return <div className="citation-text-preview"><strong>Extracted text preview</strong>{text.length?text.map(chunk=><p key={chunk.id}>{chunk.text}</p>):<p>No extracted text is available yet. Use Open original above to view or download the file.</p>}</div>;
}
