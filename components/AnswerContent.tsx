import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeSanitize from 'rehype-sanitize';
import rehypeKatex from 'rehype-katex';
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import bash from 'react-syntax-highlighter/dist/esm/languages/prism/bash';
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import {highlightNodes,highlightTerms} from '@/lib/answer-highlight';
import type {Citation} from './types';

SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('python', python);

export function completeMath(text: string): string {
  // Keep a partial streamed expression literal until its closing delimiter arrives.
  const dollars = (text.match(/(?<!\\)\$/g) || []).length;
  if (dollars % 2) text = text.replace(/(?<!\\)\$(?![\s\S]*\$)/, '\\$');
  return text;
}

export default function AnswerContent({ text, query='', citations=[], onCitation }: { text: string; query?: string; citations?: Citation[]; onCitation?:(citation:Citation)=>void }) {
  const terms=highlightTerms(query,text);
  const chip=(number:number)=>{
    const source=citations[number-1];
    return source?<button type="button" className="citation-chip" aria-label={`Open evidence ${number}: ${source.title}`} title={source.displaySnippet||source.title} onClick={()=>onCitation?.(source)}>{number}</button>:<span>⟦{number}⟧</span>;
  };
  return <div className="answer-text answer-content"><ReactMarkdown
    remarkPlugins={[remarkGfm, remarkMath]}
    rehypePlugins={[rehypeSanitize, [rehypeKatex, { throwOnError: false, strict: 'ignore' }]]}
    components={{
      p: ({children}) => <p>{highlightNodes(children,terms,chip)}</p>,
      li: ({children}) => <li>{highlightNodes(children,terms,chip)}</li>,
      h3: ({children}) => <h3>{highlightNodes(children,terms,chip)}</h3>,
      a: ({children, href}) => <a href={href || '#'} target="_blank" rel="noopener noreferrer">{children}</a>,
      table: ({children}) => <div className="answer-table-wrap" tabIndex={0} aria-label="Supporting table"><table>{children}</table></div>,
      th: ({children}) => <th scope="col">{children}</th>,
      code: ({children, className}) => {
        const language = /language-([\w-]+)/.exec(className || '')?.[1];
        const content = String(children).replace(/\n$/, '');
        return language ? <SyntaxHighlighter language={language} useInlineStyles={false}>{content}</SyntaxHighlighter> : <code>{children}</code>;
      },
    }}
  >{completeMath(text)}</ReactMarkdown></div>;
}
