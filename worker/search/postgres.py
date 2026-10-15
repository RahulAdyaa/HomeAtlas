"""Tenant-scoped PostgreSQL channels; separate connections execute concurrently."""
import re
from concurrent.futures import ThreadPoolExecutor
import psycopg
from psycopg.rows import dict_row
from .common import CONFIG, Hit, tokens, normalize
from . import word, fuzzy
from .fusion import assemble

BASE = """SELECT c.*,s.title,s.location_path FROM chunks c
 JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id AND s.current_version_id=c.version_id
 JOIN memberships m ON m.household_id=c.household_id AND m.user_id=%s
 WHERE c.household_id=%s AND s.status='ready' AND coalesce(c.metadata->>'active','true')='true'
 AND (%s OR (coalesce(c.metadata->>'sample','false')<>'true' AND s.title !~* '^SAMPLE[[:space:]—:-]'))
 AND (%s::uuid IS NULL OR c.item_id=%s::uuid) AND (%s::uuid IS NULL OR c.room_id=%s::uuid)"""

def params(household,actor,question,item,room):
    return (actor,household,bool(re.search(r'\b(sample|demo|demonstration|example)\b',question,re.I)),item,item,room,room)

def channel(name, question, scope, cfg, engine, config=CONFIG):
    terms=tokens(question)
    numeric=[w for w in terms if any(c.isdigit() for c in w)]
    base=BASE+" AND regexp_split_to_array(c.search_text,' ') @> %s::text[]"
    scope=(*scope,numeric)
    if not terms: return [],[]
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        if name=='dense':
            vectors=engine.embed_text([normalize(question)],query=True)
            if not vectors:return [],[]
            vector='['+','.join(map(str,vectors[0]))+']'
            rows=conn.execute('WITH scoped AS MATERIALIZED ('+base+''') SELECT *,1-(search_vector <=> %s::vector) AS score
                FROM scoped WHERE embedding_model=%s AND vector_dims(search_vector)=%s
                ORDER BY search_vector <=> %s::vector,id LIMIT %s''',(*scope,vector,engine.text_identity,len(vectors[0]),vector,config['channel_top_k'])).fetchall()
            rows=[d for d in rows if d['score']>=config['dense_min']]
            return [Hit(str(d['id']),d['score']) for d in rows],rows
        if name=='visual':
            vector=engine.embed_image_space(text=question)
            if not vector:return [],[]
            literal='['+','.join(map(str,vector))+']'
            rows=conn.execute('WITH scoped AS MATERIALIZED ('+BASE+"""), pages AS (
                SELECT *,row_number() OVER (
                    PARTITION BY source_id,version_id,page,coalesce(image_path,id::text)
                    ORDER BY coalesce(metadata->>'ocr_context','false')='true' DESC,length(text) DESC,id DESC
                ) AS visual_page_rank FROM scoped
                WHERE image_embedding_model=%s AND cardinality(image_embedding)=%s
                ) SELECT *,1-(image_embedding::vector <=> %s::vector) score FROM pages
                WHERE visual_page_rank=1
                ORDER BY image_embedding::vector <=> %s::vector,id LIMIT %s""",(*scope[:-1],engine.image_identity,len(vector),literal,literal,config['channel_top_k'])).fetchall()
            rows=[d for d in rows if d['score']>=config['visual']['text_min']]
            return [Hit(str(d['id']),d['score']) for d in rows],rows
        if name=='word':
            # OR terms: a typo must not eliminate correctly spelled evidence terms.
            tsquery=' | '.join("'"+w.replace("'","''")+"'" for w in terms)
            rows=conn.execute('WITH scoped AS ('+base+''') SELECT * FROM scoped
                WHERE search_terms @@ to_tsquery('simple',%s)
                ORDER BY ts_rank_cd(search_terms,to_tsquery('simple',%s)) DESC,id LIMIT %s''',(*scope,tsquery,tsquery,max(120,config['channel_top_k']))).fetchall()
            return word.search(question,rows,engine,config['channel_top_k']),rows
        rows=conn.execute('WITH scoped AS ('+base+''') SELECT *,
            (SELECT max(word_similarity(t,search_text)) FROM unnest(%s::text[]) t) AS score
            FROM scoped WHERE EXISTS(SELECT 1 FROM unnest(%s::text[]) t WHERE word_similarity(t,search_text)>=0.2 OR
                (length(t)>=3 AND t !~ '[0-9]' AND EXISTS (
                  SELECT 1 FROM unnest(regexp_split_to_array(search_text,' ')) w
                  WHERE abs(length(t)-length(w))<=2 AND length(w)>=3 AND w !~ '[0-9]'
                  AND levenshtein_less_equal(left(t,255),left(w,255),2)<=2)))
            ORDER BY score DESC,id LIMIT %s''',(*scope,terms,terms,max(120,config['channel_top_k']))).fetchall()
        return fuzzy.search(question,rows,engine,config['channel_top_k']),rows

def retrieve(question,household,actor,item,room,cfg,engine,config=CONFIG):
    scope=params(household,actor,question,item,room)
    names=['dense','word','fuzzy']+(['visual'] if config.get('visual',{}).get('enabled',False) else [])
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures={name:executor.submit(channel,name,question,scope,cfg,engine,config) for name in names}
        data={name:f.result() for name,f in futures.items()}
    documents={str(d['id']):d for _,rows in data.values() for d in rows}
    rankings={name:hits for name,(hits,_) in data.items()}
    candidates=assemble(question,list(documents.values()),rankings,engine,config)
    return candidates, list(documents.values())
