import { Fragment } from 'react';

// Render a small, safe Markdown subset. Uploaded/model text never becomes HTML.
function inline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : <Fragment key={i}>{part}</Fragment>);
}
export default function AnswerContent({ text }: { text: string }) {
  const lines = text.split('\n');
  const blocks = [];
  for (let i = 0; i < lines.length;) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    if (/^#{1,3} /.test(line)) { blocks.push(<h3 key={i}>{inline(line.replace(/^#{1,3} /, ''))}</h3>); i++; continue; }
    if (line.includes('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1] || '')) {
      const key = i;
      const cells = (row: string) => row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
      const headers = cells(line); i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes('|') && lines[i].trim()) rows.push(cells(lines[i++]));
      blocks.push(<div className="answer-table-wrap" key={key} tabIndex={0} aria-label="Supporting table"><table><thead><tr>{headers.map((c, j) => <th scope="col" key={j}>{inline(c)}</th>)}</tr></thead><tbody>{rows.map((r, j) => <tr key={j}>{headers.map((_, k) => <td key={k}>{inline(r[k] || '')}</td>)}</tr>)}</tbody></table></div>);
      continue;
    }
    const key = i, paragraph = [];
    while (i < lines.length && lines[i].trim() && !/^#{1,3} /.test(lines[i])) {
      if (i > key && lines[i].includes('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1] || '')) break;
      paragraph.push(lines[i++]);
    }
    blocks.push(<p key={key}>{inline(paragraph.join('\n'))}</p>);
  }
  return <div className="answer-text answer-content">{blocks}</div>;
}
