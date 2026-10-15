import math
import re
import time
from pathlib import Path

import numpy as np
import psycopg
from psycopg.rows import dict_row

from .config import Settings, settings
from .ingestion import ocr_image, validate_file
from .models import LocalModels, models

STOPWORDS = set('which what when where who why how is are was were a an the and or of in on to for my me does do can you this that it with from about tell show please'.split())


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r'[a-z0-9][a-z0-9-]*', text.lower()) if word not in STOPWORDS]


def lexical_scores(question: str, documents: list[dict]) -> list[float]:
    query = set(tokens(question))
    docs = [tokens(d['text']) for d in documents]
    if not docs:
        return []
    average = max(1, sum(map(len, docs)) / len(docs))
    frequency = {word: sum(word in d for d in docs) for word in query}
    scores = []
    for words in docs:
        score = 0
        for word in query:
            count = words.count(word)
            idf = math.log(1 + (len(docs) - frequency[word] + .5) / (frequency[word] + .5))
            score += idf * count * 2.2 / (count + 1.2 * (.25 + .75 * len(words) / average))
        scores.append(score)
    return scores


def rank_candidates(question: str, documents: list[dict], engine: LocalModels = models, image: Path | None = None) -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor
    from .search.fusion import CHANNELS, assemble
    from .search.common import CONFIG, numeric_matches
    from .search.visual import search
    channels=dict(CHANNELS)
    if CONFIG.get('visual',{}).get('enabled',False):
        channels['visual']=lambda q,docs,eng,limit:search(q,docs,eng,limit,image)
    text_documents=[d for d in documents if numeric_matches(question,d)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures={name:executor.submit(fn,question,documents if name=='visual' else text_documents,engine,CONFIG['channel_top_k']) for name,fn in channels.items()}
        rankings={name:f.result() for name,f in futures.items()}
    return assemble(question,documents,rankings,engine)


def citation(row: dict, index: int, quote: str) -> dict:
    return {'id': str(row['id']), 'sourceId': str(row['source_id']), 'versionId': str(row['version_id']),
            'title': row['title'], 'page': row.get('page'), 'bbox': row.get('bbox'), 'text': quote,
            'start': row.get('start_seconds'), 'end': row.get('end_seconds'), 'modality': row.get('modality', 'text'),
            'metadata': row.get('metadata', {}), 'number': index}


def answer_from_evidence(question: str, candidates: list[dict], engine: LocalModels = models,
                         image: Path | None = None) -> dict:
    if not candidates:
        return {'answer': "I couldn't find evidence in your household records to answer this. Add the relevant manual, receipt, or note and try again.",
                'citations': [], 'confidence': 'insufficient', 'mode': 'abstention'}
    generated = engine.generate(question, candidates, image=image)
    quotes = []
    conflict = False
    if generated is not None:
        conflict = generated.get('conflict') is True
        quote_map = {}
        for position, item in enumerate(generated.get('quotes', [])[:8]):
            if not isinstance(item, dict):
                continue
            index, quote = item.get('index'), item.get('quote')
            # No fabricated text or citation is allowed through model output.
            if type(index) is int and 0 <= index < len(candidates) and isinstance(quote, str) and 8 <= len(quote) <= 1200:
                source_text = candidates[index]['text']
                exact = quote if quote in source_text else None
                if exact is None:
                    # A model may flatten PDF line breaks; allow whitespace-only normalization,
                    # then return the exact original span for the independent Node verifier.
                    pattern = r'\s+'.join(re.escape(part) for part in quote.split())
                    matched = re.search(pattern, source_text) if pattern else None
                    exact = matched.group(0) if matched else None
                if exact:
                    quote_map[position] = len(quotes)
                    quotes.append((candidates[index], exact))
        if generated.get('insufficient') is True:
            quotes = []
        mode = 'local-model-grounded'
    else:
        mode = 'extractive'
        # Explicit degraded mode: only return quoted matching records, never a fabricated synthesis.
        for candidate in candidates[:2]:
            if candidate['text'] and candidate.get('lexical_score', 0) > 0:
                quotes.append((candidate, candidate['text'][:900]))
    if not quotes:
        return {'answer': 'The available records do not contain enough direct evidence to answer confidently.',
                'citations': [], 'confidence': 'insufficient', 'mode': 'abstention'}
    intro = 'These records may conflict; confirm the applicable version before relying on them.' if conflict else 'Your records say:'
    answer = intro + '\n\n' + '\n\n'.join(f'“{quote}” [{i + 1}]' for i, (_, quote) in enumerate(quotes))
    sections = []
    accepted = []
    if generated and quotes and hasattr(engine, 'verify_sections'):
        for section in generated.get('sections', [])[:8]:
            if not isinstance(section, dict):
                continue
            references = section.get('evidence')
            if (not isinstance(references, list) or not references or
                    any(type(i) is not int or i not in quote_map for i in references)):
                continue
            text, heading = section.get('text'), section.get('heading', '')
            if not isinstance(text, str) or len(text) > 4000 or not isinstance(heading, str):
                continue
            # Citation numbers are assigned by the server, never trusted from generated prose.
            text = re.sub(r'\[\d+\]', '', text).strip()
            table = section.get('table', {})
            if isinstance(table, dict):
                columns, rows = table.get('columns', []), table.get('rows', [])
                if (isinstance(columns, list) and 1 <= len(columns) <= 8 and all(isinstance(c, str) for c in columns) and
                        isinstance(rows, list) and 1 <= len(rows) <= 20 and
                        all(isinstance(r, list) and len(r) == len(columns) and all(isinstance(c, str) for c in r) for r in rows)):
                    clean = lambda cell: cell.replace('|', '/').replace('\n', ' ')[:300]
                    lines = ['| ' + ' | '.join(clean(c) for c in columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |']
                    lines.extend('| ' + ' | '.join(clean(c) for c in r) + ' |' for r in rows)
                    text += '\n\n' + '\n'.join(lines)
            if not text.strip() or len(text) > 12000:
                continue
            quoted_text = ' '.join(quotes[quote_map[i]][1] for i in references)
            # Reject common speculative additions that were not actually stated in the sources.
            if any(re.search(pattern, text, re.I) and not re.search(pattern, quoted_text, re.I)
                   for pattern in (r'\blikely\b', r'\bintended\b', r'\bdesigned for\b', r'\bproportion\w*\b', r'\blinear relationship\b')):
                continue
            sections.append({'heading': heading[:160], 'text': text,
                             'evidence': sorted(set(quote_map[i] for i in references))})
        verified = engine.verify_sections(question, sections, [
            {'index': i, 'text': quote, 'image_path': row.get('image_path'), 'page': row.get('page'), 'bbox': row.get('bbox'), 'metadata': row.get('metadata',{})}
            for i, (row, quote) in enumerate(quotes)]) if sections else []
        accepted = [sections[i] for i in sorted(set(verified)) if type(i) is int and 0 <= i < len(sections)]
        if accepted:
            answer = ('These records may conflict; confirm the applicable version before relying on them.\n\n' if conflict else '')
            answer += '\n\n'.join((f'### {s["heading"]}\n\n' if s['heading'] else '') + s['text'] + '\n\n' +
                                    ' '.join(f'[{i + 1}]' for i in s['evidence']) for s in accepted)
            if len(accepted) < len(generated.get('sections', [])):
                answer += '\n\nSome proposed details could not be verified against these records and have been omitted.'
            mode = 'local-model-explained'
    if generated and not accepted and hasattr(engine, 'verify_sections'):
        # Exact substring checks only prove provenance. Independently review a
        # quote-only fallback for responsiveness too; nearby true facts must not
        # become a confident answer to a missing attribute/object question.
        fallbacks = [{'heading': '', 'text': quote, 'evidence': [i]} for i, (_, quote) in enumerate(quotes)]
        verified = engine.verify_sections(question, fallbacks, [
            {'index': i, 'text': quote, 'image_path': row.get('image_path'), 'page': row.get('page'),
             'bbox': row.get('bbox'), 'metadata': row.get('metadata', {})}
            for i, (row, quote) in enumerate(quotes)])
        valid = sorted({i for i in verified if type(i) is int and 0 <= i < len(quotes)})
        if not valid:
            return {'answer': 'The available records do not contain enough direct evidence to answer confidently.',
                    'citations': [], 'confidence': 'insufficient', 'mode': 'abstention'}
        quotes = [quotes[i] for i in valid]
        answer = intro + '\n\n' + '\n\n'.join(f'“{quote}” [{i + 1}]' for i, (_, quote) in enumerate(quotes))
    if not accepted and any((row.get('metadata') or {}).get('visual_anchor') for row,_ in quotes):
        return {'answer': 'I found a matching image, but could not verify an answer from it. Try a clearer image or add a description.',
                'confidence':'insufficient','mode':'abstention','citations':[]}
    if not accepted and re.search(r'\b(serial|aadhaar|aadhar|pan|card number|identifier)\b',question,re.I) and any(
        (row.get('metadata') or {}).get('confidence',100)<70 and row.get('image_path') for row,_ in quotes):
        return {'answer':'The identifier is not clear enough in the image to verify. Please upload a sharper close-up.',
                'confidence':'insufficient','mode':'abstention','citations':[]}
    if image and (not engine.cfg.image_model or engine.status.get('image', '').startswith('unavailable')):
        answer += '\n\nThe photo helped identify text. Visual part matching is unavailable in this profile; these quotes do not establish compatibility.'
    if re.search(r'\b(gas|electrical|wiring|structural|breaker|mains)\b', question, re.I):
        answer += '\n\nFor hazardous electrical, gas, or structural work, use a qualified professional.'
    return {'answer': answer, 'citations': [citation(row, i + 1, quote) for i, (row, quote) in enumerate(quotes)],
            'confidence': 'conflicting' if conflict else 'supported', 'mode': mode}


def unrelated_query(question: str, candidates: list[dict]) -> bool:
    """Reject an apparent hit when most distinct subject terms have no record support."""
    from .search.common import tokens, index_text, edit_distance
    requested = set(tokens(question))
    if len(requested) < 3 or not candidates:
        return False
    found = set().union(*(set(tokens(index_text(row))) for row in candidates))
    matches = sum(term in found or (len(term) >= 5 and not any(c.isdigit() for c in term) and
                  any(abs(len(term) - len(word)) <= 2 and edit_distance(term, word) <= 1 for word in found))
                  for term in requested)
    return matches / len(requested) < .5


def query_records(household_id: str, actor_id: str, question: str, item_id: str | None = None,
                  room_id: str | None = None, image_path: str | None = None,
                  cfg: Settings = settings, engine: LocalModels = models) -> dict:
    started = time.monotonic()
    with psycopg.connect(cfg.database_url, row_factory=dict_row) as conn:
        member = conn.execute('SELECT role FROM memberships WHERE household_id=%s AND user_id=%s', (household_id, actor_id)).fetchone()
        if not member:
            raise PermissionError('Household membership is required')
    image = cfg.private_path(image_path) if image_path else None
    retrieval_question = question
    if image:
        from PIL import Image
        validate_file(image, 'image/png', cfg)
        with Image.open(image) as picture:
            image_text = ' '.join(chunk.text for chunk in ocr_image(picture, cfg))
        retrieval_question += ' ' + image_text[:1500]
    from .search.postgres import retrieve, BASE, params
    candidates, documents = retrieve(retrieval_question,household_id,actor_id,item_id,room_id,cfg,engine)
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        if image:
            documents=conn.execute(BASE,params(household_id,actor_id,question,item_id,room_id)).fetchall()
            candidates=rank_candidates(retrieval_question,documents,engine,image)
        elif candidates:
            sources=list({c['source_id'] for c in candidates})
            documents=conn.execute(BASE+' AND c.source_id=ANY(%s)',(*params(household_id,actor_id,question,item_id,room_id),sources)).fetchall()
    # Include adjacent pages from the same authorized current source: definitions often refer
    # to a diagram/table on the preceding page. Never expand outside the SQL tenant/scope filter.
    from .search.suggestions import suggest
    suggestion = suggest(question,documents,candidates)
    selected_ids = {str(c['id']) for c in candidates}
    neighbors = []
    for seed in candidates:
        if seed.get('page') is None:
            continue
        for row in documents:
            if (row['source_id'] == seed['source_id'] and row['version_id'] == seed['version_id'] and
                    row.get('page') is not None and abs(row['page'] - seed['page']) <= 1 and str(row['id']) not in selected_ids):
                selected_ids.add(str(row['id']))
                neighbors.append(row)
    candidates = (candidates + neighbors)[:12]
    result = ({'answer': "I couldn't find that in your household records.",
               'citations': [], 'confidence': 'insufficient', 'mode': 'abstention'}
              if not image and not any(c.get('visual_match') and c.get('image_path') for c in candidates) and unrelated_query(question, candidates)
              else answer_from_evidence(question, candidates, engine=engine, image=image))
    if suggestion: result['suggestion']=suggestion
    # Reauthorize after a potentially long model call; revoked members receive no source content.
    with psycopg.connect(cfg.database_url) as conn:
        if not conn.execute('SELECT 1 FROM memberships WHERE household_id=%s AND user_id=%s', (household_id, actor_id)).fetchone():
            raise PermissionError('Household membership was removed')
    if member['role'] == 'owner':
        result['diagnostics'] = {'candidateCount': len(candidates), 'scopedChunkCount': len(documents),
                                 'models': dict(engine.status), 'latencyMs': round((time.monotonic() - started) * 1000),
                                 'retrieval': 'multilingual pgvector + word BM25 + character TF-IDF/edit distance + weighted RRF'}
    return result
