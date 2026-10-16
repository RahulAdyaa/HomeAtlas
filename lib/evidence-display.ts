export function readableSnippet(raw:string,max=440):string{
 const cleaned=raw.normalize('NFKC').replace(/\b([\p{L}]+)-\s*\n\s*(?=[\p{L}])/gu,'$1')
  .replace(/^\s*Location:\s*[^\n]*\n*/gim,'').replace(/[\t ]*\n[\t ]*/g,' ').replace(/\s+/g,' ').trim();
 const sentences=[...new Set(cleaned.split(/(?<=[.!?])\s+/).filter(Boolean))];
 const picked:string[]=[];
 for(const sentence of sentences){
  if(picked.length===3||picked.join(' ').length+sentence.length>max)break;
  if(!picked.includes(sentence))picked.push(sentence);
 }
 if(picked.length)return picked.join(' ')+(picked.length<sentences.length?' …':'');
 const boundary=cleaned.slice(0,max+1).lastIndexOf(' ');
 return boundary>50?cleaned.slice(0,boundary).trimEnd()+'…':'Open the original for the complete passage.';
}
