import {describe,expect,it} from 'vitest';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import AnswerContent from '../components/AnswerContent';
describe('safe detailed answers',()=>{
 it('renders table headers and values as accessible table cells',()=>{
  const html=renderToStaticMarkup(createElement(AnswerContent,{text:'### Modes\n\n| Mode | Power |\n| --- | --- |\n| Boost | 71 W |\n\n[1]'}));
  expect(html).toContain('<th scope="col">Mode</th>');
  expect(html).toContain('<td>71 W</td>');
  expect(html).toContain('answer-table-wrap');
 });
 it('treats source HTML and scripts as literal text',()=>{
  const html=renderToStaticMarkup(createElement(AnswerContent,{text:'<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>'}));
  expect(html).not.toContain('<script>');expect(html).not.toContain('<img');
  expect(html).toContain('&lt;script&gt;');
 });
});
