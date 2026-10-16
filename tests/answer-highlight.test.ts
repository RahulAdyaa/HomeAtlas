import {describe,it,expect} from 'vitest';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {highlightTerms,markedText} from '../lib/answer-highlight';
import AnswerContent from '../components/AnswerContent';

describe('answer keyword highlights',()=>{
 it('maps common spelling variants and preserves word boundaries',()=>{
  expect(highlightTerms('Where is my adhar card?', 'The Aadhaar card is here.')).toContain('Aadhaar');
  const html=renderToStaticMarkup(createElement('p',{},markedText('Aadhaar and AadhaarX', ['Aadhaar'])));
  expect(html).toContain('<mark>Aadhaar</mark> and AadhaarX');
 });
 it('escapes regex metacharacters and excludes math and code',()=>{
  const html=renderToStaticMarkup(createElement(AnswerContent,{query:'alpha',text:'alpha and $alpha$\n\n```python\nalpha = 2\n```'}));
  expect(html).toContain('<mark>alpha</mark>');
  expect(html.match(/<mark>/g)?.length).toBe(1);
  const literal=renderToStaticMarkup(createElement('p',{},markedText('a+b and ab', ['a+b'])));
  expect(literal).toContain('<mark>a+b</mark> and ab');
 });
});
