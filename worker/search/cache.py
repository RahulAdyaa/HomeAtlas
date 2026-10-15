"""Versioned PostgreSQL cache. Call only through authenticated worker endpoints.

Storage interface: lookup/store/clear/metrics. No query text is logged.
"""
import hashlib
import json
import re
import time
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .common import CONFIG, ALIASES, normalize, tokens, edit_distance

CONFIG_VERSION=hashlib.sha256(json.dumps([CONFIG,ALIASES,'cache-v3'],sort_keys=True).encode()).hexdigest()
FILLER=set('could would kindly tell show find locate stored kept located put know give details detail about information find out please'.split())

def numbers(query):
    return sorted(re.findall(r'\b\w*\d\w*(?:[-./]\w+)*\b',query.lower()))

def semantic_text(query, vocabulary=()):
    # Remove request phrasing, retain EVERY content term and numeric identifier.
    # Unique one-edit corrections only; never drop an unmatched object/room term.
    words=set(tokens(query))-FILLER
    canonical=[]
    for word in sorted(words):
        near=[v for v in vocabulary if len(v)>=5 and len(word)>=5 and
              not any(c.isdigit() for c in v+word) and edit_distance(word,v)<=1]
        canonical.append(near[0] if word not in vocabulary and len(near)==1 else word)
    return ' '.join(sorted(canonical))

def intent(query):
    normalized=normalize(query)
    if re.match(r'^(what is|what are|explain|describe|define) (?:a |an )?',normalized) and not re.search(r'\b(my|our|number|serial|warranty|model|brand|date)\b',normalized):return 'explanation'
    return 'record'

def guard(a,b):
    if intent(a)!=intent(b):return False
    if numbers(a)!=numbers(b):return False
    aa=set(tokens(a))-FILLER; bb=set(tokens(b))-FILLER
    if len(aa)!=len(bb):return False
    remaining=set(bb)
    for word in sorted(aa,key=lambda w: (w not in bb,w)):
        if word in remaining: remaining.remove(word);continue
        matches=[w for w in remaining if len(w)>=5 and len(word)>=5 and
                 not any(c.isdigit() for c in w+word) and edit_distance(word,w)<=1]
        if len(matches)!=1:return False
        remaining.remove(matches[0])
    return not remaining

def key(query):
    return hashlib.sha256(json.dumps([normalize(query),numbers(query)],ensure_ascii=False).encode()).hexdigest()

def authorize(conn,hid,uid,owner=False):
    row=conn.execute('SELECT role FROM memberships WHERE household_id=%s AND user_id=%s',(hid,uid)).fetchone()
    if not row or (owner and row['role']!='owner'):raise PermissionError('Household access required')

def references(answer):
    refs=[]
    for c in answer.get('citations',[]):
        refs.append(dict(kind='chunk',id=c['id'],sourceId=c['sourceId'],versionId=c['versionId'],locationPath=c.get('locationPath'),text=c.get('text','')))
    for c in answer.get('locationMatches',[]):
        refs.append(dict(kind=c['kind'],id=c['id'],locationPath=c['locationPath']))
    return refs

def valid_references(conn,hid,refs):
    for ref in refs:
        if ref['kind']=='chunk':
            row=conn.execute('''SELECT s.location_path,c.text FROM chunks c JOIN sources s ON s.id=c.source_id AND s.household_id=c.household_id
                WHERE c.household_id=%s AND c.id=%s AND s.id=%s AND c.version_id=%s AND s.current_version_id=c.version_id
                AND s.status='ready' AND coalesce(c.metadata->>'active','true')='true' ''',(hid,ref['id'],ref['sourceId'],ref['versionId'])).fetchone()
            if not row or ref['text'] not in row['text']:return False
        else:
            table={'item':'items','source':'sources'}.get(ref['kind'])
            if not table:return False
            row=conn.execute(f'SELECT location_path FROM {table} WHERE household_id=%s AND id=%s',(hid,ref['id'])).fetchone()
        if not row or row['location_path']!=ref.get('locationPath'):return False
    return True

def metric(conn,hid,uid,kind,lookup_ms,saved=0,rejected=0,candidates=0):
    assert kind in ('exact_hits','semantic_hits','misses')
    conn.execute(f'''INSERT INTO cache_metrics(household_id,user_id,{kind},lookup_ms,saved_ms,guard_rejections,semantic_candidates)
        VALUES(%s,%s,1,%s,%s,%s,%s) ON CONFLICT(household_id,user_id) DO UPDATE SET
        {kind}=cache_metrics.{kind}+1,lookup_ms=cache_metrics.lookup_ms+excluded.lookup_ms,
        saved_ms=cache_metrics.saved_ms+excluded.saved_ms,guard_rejections=cache_metrics.guard_rejections+excluded.guard_rejections,
        semantic_candidates=cache_metrics.semantic_candidates+excluded.semantic_candidates''',(hid,uid,lookup_ms,saved,rejected,candidates))

def lookup(hid,uid,query,scope,cfg,engine,bypass=False):
    start=time.monotonic(); config=CONFIG['cache']; embedding=None; rejected=0; candidates=0
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        authorize(conn,hid,uid)
        version=conn.execute('SELECT data_version FROM households WHERE id=%s',(hid,)).fetchone()['data_version']
        result={'hit':False,'dataVersion':str(version),'configVersion':CONFIG_VERSION}
        if bypass or not config['enabled']:return result
        args=(hid,uid,version,CONFIG_VERSION,scope)
        base='''SELECT * FROM answer_cache WHERE household_id=%s AND user_id=%s AND data_version=%s
                AND config_version=%s AND scope_key=%s AND expires_at>now()'''
        row=conn.execute(base+' AND query_key=%s',(*args,key(query))).fetchone()
        kind='exact'
        if not row:
            vocabulary=set()
            for prior in conn.execute(base,args).fetchall():vocabulary.update(tokens(prior['query']))
            vectors=engine.embed_text([semantic_text(query,vocabulary)],query=True)
            embedding=vectors[0] if vectors else None
            if embedding:
                vector='['+','.join(map(str,embedding))+']'
                rows=conn.execute(base+''' AND embedding_model=%s AND vector_dims(embedding)=%s
                    ORDER BY embedding <=> %s::vector LIMIT 5''',(*args,engine.text_identity,len(embedding),vector)).fetchall()
                import numpy as np
                for candidate in rows:
                    v=json.loads(candidate['embedding'])
                    similarity=float(np.dot(embedding,v)/(max(1e-12,np.linalg.norm(embedding)*np.linalg.norm(v))))
                    if similarity<config['similarity']:continue
                    candidates+=1
                    if guard(query,candidate['query']):row=candidate;kind='semantic';break
                    rejected+=1
        # Lock version through validation/touch. Mutations bump the same row.
        current=conn.execute('SELECT data_version FROM households WHERE id=%s FOR SHARE',(hid,)).fetchone()['data_version']
        authorize(conn,hid,uid)
        elapsed=(time.monotonic()-start)*1000
        if row and current==version and guard(query,row['query']) and valid_references(conn,hid,row['references_json']):
            conn.execute('UPDATE answer_cache SET hit_count=hit_count+1,last_used_at=now() WHERE id=%s',(row['id'],))
            metric(conn,hid,uid,kind+'_hits',elapsed,max(0,row['latency_ms']-elapsed),rejected,candidates)
            return dict(result,hit=True,kind=kind,answer=row['answer'])
        metric(conn,hid,uid,'misses',elapsed,rejected=rejected,candidates=candidates)
        return result

def store(hid,uid,query,scope,version,answer,latency,cfg,engine):
    if not CONFIG['cache']['enabled']:return False
    refs=references(answer)
    if answer.get('confidence')!='insufficient' and not refs:return False
    vectors=engine.embed_text([semantic_text(query)],query=True)
    vector='['+','.join(map(str,vectors[0]))+']' if vectors else None
    ttl=CONFIG['cache']['negative_ttl_seconds'] if answer.get('confidence')=='insufficient' else CONFIG['cache']['ttl_seconds']
    # Diagnostics and request-specific accounting must never be replayed as answer data.
    answer={k:v for k,v in answer.items() if k in ('answer','citations','confidence','mode','locationMatches','recordFacts','suggestion')}
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        authorize(conn,hid,uid)
        current=conn.execute('SELECT data_version FROM households WHERE id=%s FOR UPDATE',(hid,)).fetchone()['data_version']
        if str(current)!=str(version) or not valid_references(conn,hid,refs):return False
        conn.execute('''INSERT INTO answer_cache(household_id,user_id,data_version,config_version,scope_key,query_key,query,
            embedding,embedding_model,answer,references_json,latency_ms,expires_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s::vector,%s,%s,%s,%s,now()+%s*interval '1 second')
            ON CONFLICT(household_id,user_id,data_version,config_version,scope_key,query_key) DO UPDATE SET
            answer=excluded.answer,references_json=excluded.references_json,embedding=excluded.embedding,
            expires_at=excluded.expires_at,last_used_at=now(),latency_ms=excluded.latency_ms''',
            (hid,uid,version,CONFIG_VERSION,scope,key(query),query,vector,engine.text_identity,Jsonb(answer),Jsonb(refs),latency,ttl))
        conn.execute('DELETE FROM answer_cache WHERE household_id=%s AND user_id=%s AND (data_version<>%s OR expires_at<=now())',(hid,uid,current))
        conn.execute('''DELETE FROM answer_cache WHERE id IN (SELECT id FROM answer_cache WHERE household_id=%s AND user_id=%s
            ORDER BY last_used_at DESC,id OFFSET %s)''',(hid,uid,CONFIG['cache']['max_entries_per_user']))
    return True

def clear(hid,uid,cfg):
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        authorize(conn,hid,uid,owner=True)
        # Increment also prevents in-flight queries repopulating the cleared generation.
        conn.execute('UPDATE households SET data_version=data_version+1 WHERE id=%s',(hid,))
        count=conn.execute('DELETE FROM answer_cache WHERE household_id=%s',(hid,)).rowcount
        return {'cleared':count}

def metrics(hid,uid,cfg):
    with psycopg.connect(cfg.database_url,row_factory=dict_row) as conn:
        authorize(conn,hid,uid,owner=True)
        row=conn.execute('''SELECT coalesce(sum(exact_hits),0)::float exact_hits,coalesce(sum(semantic_hits),0)::float semantic_hits,
            coalesce(sum(misses),0)::float misses,coalesce(sum(saved_ms),0)::float saved_ms,
            coalesce(sum(guard_rejections),0)::float guard_rejections,coalesce(sum(semantic_candidates),0)::float semantic_candidates
            FROM cache_metrics WHERE household_id=%s''',(hid,)).fetchone()
        total=row['exact_hits']+row['semantic_hits']+row['misses']; hits=row['exact_hits']+row['semantic_hits']
        return dict(row,exactHitRate=row['exact_hits']/max(1,total),semanticHitRate=row['semantic_hits']/max(1,total),
                    averageLatencySavedMs=row['saved_ms']/max(1,hits),
                    guardRejectionRate=row['guard_rejections']/max(1,row['semantic_candidates']),
                    falseHitRate=None,falseHitRateNote='Requires labeled evaluation; guard rejections are prevented hits, not observed false hits.')
