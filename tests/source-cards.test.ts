import {describe,it,expect} from 'vitest';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import SourceCards from '../components/SourceCards';
import AnswerContent from '../components/AnswerContent';
import {readableSnippet} from '../lib/evidence-display';

const citation={id:'chunk1',sourceId:'source1',versionId:'version1',title:'QLoRA paper.pdf',page:4,
 text:'Location: Living room\n\nQLoRA uses 4-bit quantization. QLoRA uses 4-bit quantization. Later details follow.',
 locationPath:'Living room > Desk > Top drawer',locationUrl:'/home?location=desk',number:1};

describe('source evidence display',()=>{
 it('cleans metadata, deduplicates snippets, and stops at sentence boundaries',()=>{
  expect(readableSnippet(citation.text)).toBe('QLoRA uses 4-bit quantization. Later details follow.');
  expect(readableSnippet('A long complete sentence. Extra sentence here.',26)).toBe('A long complete sentence. …');
 });
 it('shows one document card and distinct server citation chips',()=>{
  const cards=renderToStaticMarkup(createElement(SourceCards,{citations:[citation,{...citation,id:'chunk2',page:5,number:2}],query:'What is quantization?',onOpen:()=>{},scopedPath:(x:string)=>x}));
  expect(cards.match(/class="source-card"/g)?.length).toBe(1);
  expect(cards).toContain('Living room &gt; Desk &gt; Top drawer');
  expect(cards).toContain('Pages 4, 5');
  expect(cards).not.toContain('Location:');
  const answer=renderToStaticMarkup(createElement(AnswerContent,{text:'QLoRA works ⟦1⟧; the paper references [28].',citations:[citation],onCitation:()=>{}}));
  expect(answer).toContain('class="citation-chip"');
  expect(answer).toContain('[28]');
 });
});
