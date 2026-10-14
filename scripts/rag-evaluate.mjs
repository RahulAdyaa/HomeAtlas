import {request} from '@playwright/test';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const context=await request.newContext({baseURL:'http://localhost:3000',storageState:'.data/journey-session.json',extraHTTPHeaders:{Origin:'http://localhost:3000'}});
const a=await(await context.get('/api/atlas')).json();if(!a.household)throw new Error('Run the complete browser journey first.');
const cases=[
 {name:'filter',question:'Which replacement filter fits the AirOne AP-200?',source:'AirOne-AP200-manual.pdf',page:2,quote:'A200-HEPA'},
 {name:'warranty',question:'When does the AirOne AP-200 warranty expire?',source:'AirOne-purchase-receipt.pdf',page:1,quote:'12 February 2028'},
 {name:'reset',question:'How does the AirOne AP-200 filter reminder reset work?',source:'AirOne-AP200-manual.pdf',page:2,quote:'5 seconds'},
 {name:'missing',question:'What is the exact tariff on my latest electricity bill?',abstain:true},
 {name:'photo',question:'Which replacement filter is described in this photo of the AirOne AP-200 manual?',source:'AirOne-AP200-manual.pdf',page:2,quote:'A200-HEPA',image:true},
];
const results=[];
for(const item of cases){const started=Date.now();const multipart={question:item.question,itemId:a.items.find(i=>i.name==='Bedroom air purifier')?.id||'',operationId:crypto.randomUUID(),...(item.image?{image:{name:'filter-page-photo.png',mimeType:'image/png',buffer:await fs.readFile('tests/fixtures/filter-page-photo.png')}}:{})};const r=await context.post('/api/ask',{multipart,timeout:180000});if(!r.ok())throw new Error(`${item.name}: HTTP ${r.status()}`);const reply=await r.json();let correct=true;for(const c of reply.citations){const evidence=await(await context.get('/api/citations/'+c.id)).json();correct=correct&&evidence.text.includes(c.text)&&evidence.versionId===c.versionId&&evidence.page===c.page;}
 const retrieval=item.abstain?reply.citations.length===0:reply.citations.some(c=>c.title===item.source&&c.page===item.page);
 const grounded=item.abstain?reply.confidence==='insufficient':reply.answer.includes(item.quote)&&reply.citations.some(c=>c.text.includes(item.quote));
 results.push({case:item.name,sourceRecall:retrieval,citationCorrectness:correct,groundedness:grounded,abstention:reply.confidence==='insufficient',mode:reply.mode,latencyMs:Date.now()-started,models:reply.diagnostics?.models});console.log(item.name,reply.mode,`${Date.now()-started}ms`,retrieval&&grounded&&correct?'PASS':'FAIL');
}
const supported=results.filter(r=>r.case!=='missing'),report={date:'2026-10-13',cases:results,sourceRecall:supported.filter(r=>r.sourceRecall).length/supported.length,citationCorrectness:results.filter(r=>r.citationCorrectness).length/results.length,groundedness:results.filter(r=>r.groundedness).length/results.length,missingEvidenceAbstention:results.find(r=>r.case==='missing').abstention};
await fs.writeFile('docs/rag-results.json',JSON.stringify(report,null,2));console.log('Saved measured evaluation to docs/rag-results.json.');await context.dispose();if(results.some(r=>!r.sourceRecall||!r.citationCorrectness||!r.groundedness))process.exitCode=1;
