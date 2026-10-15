"""Groups E/H/I: real authenticated API checks against disposable fictional records.

No customer household is queried. Administrative SQL is limited to fixture account,
fixture credit/rate fixtures, and cleanup. No application logic is patched.
"""
from __future__ import annotations
import json, os, re, sys, time, uuid, statistics, fcntl
from pathlib import Path
from contextlib import nullcontext
import requests
import psycopg
from psycopg.rows import dict_row
from dotenv import dotenv_values
from protocol import argument_parser, make_result, write_result as protocol_write_result, metric, shared_generation_slot, frozen_dataset, cache_key

HERE=Path(__file__).resolve().parent
MAIN=Path(os.environ.get('EVAL_APP_ROOT','/Users/rahuladya/Documents/New project/homeatlas'))
ORIGIN=os.environ.get('EVAL_APP_URL','http://localhost:3000')
def write_result(path,result):
    lockdir=MAIN/'evaluation/runtime/coordination';lockdir.mkdir(parents=True,exist_ok=True)
    with (lockdir/'homeatlas-result.lock').open('a+') as h:
        fcntl.flock(h,fcntl.LOCK_EX)
        try:
            validate_field_facts(result)
            validate_cache_answers(result)
            protocol_write_result(path,result)
        finally:fcntl.flock(h,fcntl.LOCK_UN)
os.environ.setdefault('EVAL_SHARED_RUNTIME',str(MAIN/'evaluation/runtime'))
os.environ.setdefault('MODEL_DIR',str(MAIN/'data/models'))
class API:
    def __init__(self):
        env={**dotenv_values(MAIN/'.env'),**dotenv_values(MAIN/'.env.local'),**os.environ}
        self.db=psycopg.connect(env['DATABASE_URL'],autocommit=True,row_factory=dict_row)
        self.worker_key=env['WORKER_KEY'];self.session=requests.Session();self.session.headers['Origin']=ORIGIN
        self.actor=None;self.hid=None;self.rows=[];self.uploads=[];self.lock_wait_ms=0;self.last_ask=0;self.last_upload=0
    def sql(self,query,args=()):return self.db.execute(query,args)
    def call(self,path,body=None,method='POST',worker=False,files=None):
        start=time.monotonic();base='http://127.0.0.1:8001' if worker else ORIGIN
        headers={'x-worker-key':self.worker_key} if worker else {}
        if not worker and path.startswith('/api/ask'):
            self.last_ask=time.monotonic()
        kwargs={'headers':headers,'timeout':300}
        if files:kwargs.update(data=body,files=files)
        elif body is not None:kwargs['json']=body
        response=self.session.request(method,base+path,**kwargs)
        try:data=response.json()
        except ValueError:data={'error':'non-json response'}
        return {'status':response.status_code,'body':data,'latency_ms':(time.monotonic()-start)*1000}
    def start(self,phase,run):
        email=f'eval-homeatlas-{phase}-{run}-{uuid.uuid4()}@example.invalid';password='Evaluation-fixture-'+str(uuid.uuid4())
        up=self.call('/api/auth/sign-up/email',{'name':'Fictional evaluation fixture','email':email,'password':password})
        if up['status']>=300:raise RuntimeError('fixture sign up failed: '+str(up['status']))
        self.actor=up['body']['user']['id'];self.sql('UPDATE "user" SET "emailVerified"=true WHERE id=%s',(self.actor,))
        signed=self.call('/api/auth/sign-in/email',{'email':email,'password':password})
        if signed['status']>=300:raise RuntimeError('fixture sign in failed')
        home=self.call('/api/atlas',{'action':'createHousehold','name':'Synthetic evaluation home','starterRooms':False})
        if home['status']!=201:raise RuntimeError('fixture household failed')
        self.hid=home['body']['household']['id']
        self.sql('SELECT atlas_grant_credit(%s,%s,10000,%s)',(self.hid,'evaluation:'+str(uuid.uuid4()),self.actor))
    def location(self,body):
        result=self.call('/api/locations?householdId='+self.hid,body)
        if result['status']!=200:raise RuntimeError('fixture location setup failed: '+str(result['status']))
        return result['body']['id']
    def ask(self,id,question,*,generation=False,extra=None):
        time.sleep(max(0,5.1-(time.monotonic()-self.last_ask)))
        start=time.monotonic()
        with shared_generation_slot() if generation else nullcontext():
            wait=(time.monotonic()-start)*1000
            result=self.call('/api/ask?householdId='+self.hid,{'question':question,'operationId':str(uuid.uuid4()),**(extra or {})})
        result.update(id=id,question=question,group='E',generation_lock_wait_ms=wait,
                      final_answer=result['body'].get('answer'),confidence=result['body'].get('confidence'),
                      mode=result['body'].get('mode'),cache=result['body'].get('cache'))
        self.rows.append(result);print('completed '+id,flush=True);return result
    def upload(self,title,text,location):
        time.sleep(max(0,4.1-(time.monotonic()-self.last_upload)))
        self.last_upload=time.monotonic()
        result=self.call('/api/sources?householdId='+self.hid,{'locationId':location,'operationId':str(uuid.uuid4())},files={'file':(title+'.txt',text.encode(),'text/plain')})
        if result['status']!=202:raise RuntimeError('fixture upload failed '+str(result['status']))
        sid=result['body']['sourceId'];started=time.monotonic()
        while time.monotonic()-started<240:
            row=self.sql('SELECT status FROM sources WHERE id=%s AND household_id=%s',(sid,self.hid)).fetchone()
            if row['status']=='ready':
                self.uploads.append(sid);return sid,(time.monotonic()-started)*1000
            if row['status']=='failed':raise RuntimeError('fixture ingestion failed')
            time.sleep(.25)
        raise RuntimeError('fixture ingestion timeout')
    def clear(self):return self.call('/api/cache?householdId='+self.hid,method='DELETE')
    def cleanup(self):
        # All paths below belong exclusively to this randomly created synthetic household.
        storage=[]
        if self.hid:
            storage=[Path(r['path']) for r in self.sql('SELECT storage_path AS path FROM source_versions WHERE household_id=%s UNION SELECT image_path AS path FROM chunks WHERE household_id=%s AND image_path IS NOT NULL',(self.hid,self.hid))]
            self.sql('DELETE FROM households WHERE id=%s',(self.hid,))
        if self.actor:
            self.sql('DELETE FROM rate_limits WHERE key=ANY(%s)',([f'ask:{self.actor}',f'upload:{self.actor}',f'atlas:{self.actor}'],))
            self.sql('DELETE FROM "user" WHERE id=%s',(self.actor,))
        for p in storage:
            if self.hid and self.hid in p.parts and p.is_file():p.unlink()
        self.db.close()

def norm(s):return re.sub('[^a-z0-9]','',str(s).lower())
def found_paths(row):
    b=row['body'];return list({x.get('locationPath') for x in b.get('locationMatches',[])+b.get('citations',[]) if x.get('locationPath')})
def contains_fact(answer,part):
    text=re.sub(r'(?<=\d),(?=\d)','',str(answer)).lower()
    chunks=re.findall(r'[a-z0-9]+',str(part).lower())
    if not chunks:return False
    pattern=r'(?<![a-z0-9])'+r'[\s\-–—]*'.join(map(re.escape,chunks))+r'(?![a-z0-9])'
    return re.search(pattern,text) is not None

def answer_has(row,*parts):return row['status']==200 and all(contains_fact(row['body'].get('answer',''),p) for p in parts)
def rate(rows,key):return sum(bool(r[key]) for r in rows)/len(rows) if rows else None

def validate_field_facts(result):
    """Require whole fact boundaries: 8000 must never match 80000."""
    for m in result['metrics']:
        if m['metric']=='E.upload_to_ready_mean_ms':m['metric']='E.upload_response_to_ready_mean_ms'
    result['config']['upload_ready_clock']='Elapsed from successful HTTP202 upload response to source.status=ready poll, excluding upload POST latency and request pacing.'
    scenario_gold={'aggregate-001':['AC-300','2027'],'aggregate-002':['58000'],'aggregate-003':['May','2028','July','2029'],
                   'follow-up-001':['May','2028'],'follow-up-002':['WM-800'],'follow-up-003':['Living room','Cabinet']}
    for row in result['per_question']:
        parts=row.get('expected_facts') or scenario_gold.get(row['id'])
        if parts:
            row['expected_facts']=parts
            if 'body'in row:row['correct']=answer_has(row,*parts)
            elif 'answer'in row:row['correct']=all(contains_fact(row['answer'].get('answer',''),p) for p in parts)
    changes=[]
    for field in ['identifier','date','amount']:
        chosen=[r for r in result['per_question'] if r.get('field')==field]
        if chosen:changes.append(metric('E.document_'+field+'_fact_presence',sum(r['correct'] for r in chosen)/len(chosen),len(chosen)))
    for typ in ['aggregate','follow-up']:
        chosen=[r for r in result['per_question'] if r.get('type')==typ]
        if chosen:changes.append(metric('E.'+typ+'_fact_presence',sum(r['correct'] for r in chosen)/len(chosen),len(chosen),scope_note='Whole-boundary fact presence only; not judge correctness. Stateless follow-ups may coincidentally mention expected facts.'))
    counter=[r for r in result['per_question'] if r['id'].startswith('cache-generated-counter-')]
    if counter:changes.append(metric('H.generated_inprocess_fact_presence',sum(r['correct'] for r in counter)/len(counter),len(counter)))
    names={m['metric'] for m in changes};result['metrics']=[m for m in result['metrics'] if m['metric']not in names]+changes
    result['config']['fact_matching']='Whole alphanumeric fact boundaries, case-insensitive, punctuation-normalized; digit thousands commas accepted. Exact saved values use string equality.'
    result['config']['capability_findings']={
        'aggregate_failed_case_ids':[r['id'] for r in result['per_question'] if r.get('type')=='aggregate' and not r.get('correct')],
        'follow_up_support':'Current /api/ask does not accept/use conversation history. Verbatim follow-ups and supplied history were sent without rewriting; matching reference facts can occur coincidentally and do not establish history support.',
        'structured_extraction':'No automatic semantic document-type or person-name extraction API output; identifier/date/amount checks are grounded source-content Q/A with no saved item metadata.',
        'numeric_trust':'Only categorical confidence is emitted; calibration metrics are NOT MEASURED.',
        'application_changes_by_this_agent':False,
        'scope':'Household scenarios and additional declared disposable cache fixtures; no PDF or customer data is read by this evaluator.'}


def validate_cache_answers(result):
    """Hitrate is independent of answer correctness; check exact source IDs and facts."""
    cfg=result['config'];expected=cfg.get('cache_expected_item')
    if not expected:
        goldpath=MAIN/'evaluation/runtime'/f"homeatlas-cache-expected-{result['phase']}-{result['run']}.json"
        if goldpath.exists():expected=json.loads(goldpath.read_text());cfg['cache_expected_item']=expected
    groups={name:[r for r in result['per_question'] if r['id'].startswith(prefix)] for name,prefix in [('exact','cache-exact-'),('variant','cache-variant-')]}
    added=[]
    for name,rows in groups.items():
        for r in rows:
            body=r.get('body',{});r['cache_hit']=body.get('cache',{}).get('hit',False)
            r['expected_item']=expected
            facts=body.get('recordFacts',[]);locations=body.get('locationMatches',[])
            r['answer_correct']=bool(expected and r.get('status')==200 and any(f.get('id')==expected['id'] and f.get('field')=='serialNumber' and f.get('value')==expected['value'] and f.get('locationPath')==expected['locationPath'] for f in facts) and any(l.get('id')==expected['id'] and l.get('kind')=='item' and l.get('locationPath')==expected['locationPath'] for l in locations))
            r['correct']=r['answer_correct']
            r['correct_answer_hit']=r['cache_hit'] and r['answer_correct']
        if rows:
            added.extend([metric('H.'+name+'_hit_rate',sum(r['cache_hit'] for r in rows)/len(rows),len(rows)),
                          metric('H.'+name+'_answer_accuracy',sum(r['answer_correct'] for r in rows)/len(rows),len(rows)),
                          metric('H.'+name+'_correct_answer_hit_rate',sum(r['correct_answer_hit'] for r in rows)/len(rows),len(rows))])
    replace={m['metric'] for m in added};result['metrics']=[m for m in result['metrics'] if m['metric'] not in replace]+added
    cfg['cache_correctness_method']='Hit rate and answer correctness are separate. Correct answer requires stored fixture item ID, exact serial value, and expected location in both recordFacts and locationMatches.'

def evaluate(args):
    frozen_dataset();dataset=json.loads((HERE/'scenarios.json').read_text());api=API();metrics=[];config={
        'groups':['E','H','I'],'transport':'authenticated HTTP /api/ask + /api/cache, private authenticated cache lookup for near misses',
        'origin':ORIGIN,'fixture_only_rate_limit_reset':False,'http_pacing':'Ask requests spaced >=5.1sec and uploads >=4.1sec; pacing excluded from HTTP latency','synthetic_only':True,
        'cache_latency_note':'Wall HTTP latency excludes shared_generation_slot queue and pacing. Saved-fact paths avoid generation. First request is warmup and reported separately; saved-fact savings do not establish generated-answer savings.',
        'judge_model':None,'automatic_extraction_note':'Document Q/A uses ingested text only; no item metadata populated until cache stage.',
        'extra_smoke_tests':'Location, duplicate and cache checks derive from frozen scenario documents; all added fixtures are fictional.',
        'history_note':'Endpoint receives frozen question/history exactly, does not implement history; no rewriting performed.'}
    try:
        api.start(args.phase,args.run)
        locations={dataset['hierarchy'][0]['id']:api.hid};paths={}
        for node in dataset['hierarchy'][1:]:
            loc=api.location({'action':'create','type':node['type'],'parentId':locations[node['parent_id']],'name':node['name']})
            locations[node['id']]=loc;paths[node['location_path']]=loc
        source_map={};upload_rows=[]
        for doc in dataset['documents']:
            sid,elapsed=api.upload(doc['title'],doc['text'],locations[doc['location_id']]);source_map[doc['id']]=sid
            upload_rows.append({'id':'upload-'+doc['key'],'upload_to_ready_ms':elapsed,'source_id':sid,'gold_location_path':doc['location_path'],'group':'E','synthetic':True})
            print('ingested '+doc['key'],flush=True)
        api.rows+=upload_rows
        # Exact source location lookup. Three levels are evaluated only when gold has them.
        location_rows=[]
        for doc in dataset['documents']:
            row=api.ask('location-'+doc['key'],'Where is my '+doc['title']+'?',extra={'bypassCache':True})
            row['gold_location_path']=doc['location_path'];row['source_fixture_id']=doc['id'];actual=found_paths(row);gold=doc['location_path'].split(' > ')
            for level,name in [(1,'room'),(2,'zone'),(3,'container')]:
                if len(gold)>=level:row[name+'_correct']=any(p.split(' > ')[:level]==gold[:level] for p in actual)
            row['full_path_correct']=doc['location_path'] in actual
            row['location_link_correct']=any(x.get('locationId')==locations[doc['location_id']] and 'location='+locations[doc['location_id']] in x.get('locationUrl','') for x in row['body'].get('locationMatches',[]))
            location_rows.append(row)
        for name in ['room','zone','container','full_path','location_link']:
            chosen=[r for r in location_rows if name+'_correct'in r];metrics.append(metric('E.'+name+'_accuracy',rate(chosen,name+'_correct'),len(chosen)))
        metrics.append(metric('E.upload_index_ready_rate',len(upload_rows)/len(dataset['documents']),len(dataset['documents'])))
        metrics.append(metric('E.upload_response_to_ready_mean_ms',statistics.mean(r['upload_to_ready_ms'] for r in upload_rows),len(upload_rows)))
        # Automatic document-content answers, never substituted from saved fields.
        field_tests=[('identifier-pan','What is the PAN card number?',['TESTP0001A'],'identifier'),
          ('identifier-aadhaar','What is my Aadhaar card serial number?',['0000 1111 2222'],'identifier'),
          ('identifier-router','What model is the router?',['RT-400'],'identifier'),
          ('date-fridge','When does the fridge warranty expire?',['May','2028'],'date'),
          ('date-washer','When does the washing machine warranty expire?',['July','2029'],'date'),
          ('amount-microwave','How much was paid for the microwave?',['8000'],'amount'),
          ('amount-laptop','How much was paid for the laptop?',['50000'],'amount')]
        field_rows=[]
        for id,q,parts,field in field_tests:
            row=api.ask(id,q,generation=True,extra={'bypassCache':True});row.update(field=field,expected_facts=parts,correct=answer_has(row,*parts),saved_metadata_used=bool(row['body'].get('recordFacts')));field_rows.append(row)
        for field in ['identifier','date','amount']:
            chosen=[r for r in field_rows if r['field']==field];metrics.append(metric('E.document_'+field+'_fact_presence',rate(chosen,'correct'),len(chosen)))
        metrics.append(metric('E.document_type_extraction',None,0,reason='API emits MIME type and supplied filename, but has no automatic semantic document-type extraction output. No metadata value substituted.'))
        metrics.append(metric('E.document_name_extraction',None,0,reason='Frozen household records contain no ground-truth person-name fields, and API has no automatic structured person-name extraction output.'))
        scenario_rows=[]
        for q in dataset['questions']:
            if q['type'] not in ['aggregate','follow-up']:continue
            row=api.ask(q['id'],q['question'],generation=True,extra={'bypassCache':True,**({'history':q['history']} if q.get('history') else {})})
            row.update(type=q['type'],history=q.get('history'),reference_answer=q['reference_answer'],relevant_document_ids=q['relevant_document_ids'])
            expected={'aggregate-001':['AC-300','2027'],'aggregate-002':['58000'],'aggregate-003':['May','2028','July','2029'],
                      'follow-up-001':['May','2028'],'follow-up-002':['WM-800'],'follow-up-003':['Living room','Cabinet']}[q['id']]
            row['correct']=answer_has(row,*expected);row['history_supported']=False if q['type']=='follow-up' else None;scenario_rows.append(row)
        for typ in ['aggregate','follow-up']:
            chosen=[r for r in scenario_rows if r['type']==typ];metrics.append(metric('E.'+typ+'_fact_presence',rate(chosen,'correct'),len(chosen),scope_note='Fact presence only; not LLM-judged correctness. Follow-ups are stateless and may coincidentally find matching facts.'))
        metrics.append(metric('E.follow_up_history_support',0,3,reason='The current /api/ask route ignores history/conversation parameters; frozen follow-ups were sent verbatim with history, never expanded.'))
        # Time an actually generated document answer with cache on/off, independently of saved fields.
        gen_seed=api.ask('cache-generated-prime','When does the fridge warranty expire?',generation=True);gen_seed['group']='H'
        gen_hit=api.ask('cache-generated-exact','When does the fridge warranty expire?',generation=True);gen_hit['group']='H'
        metrics.extend([metric('H.generated_prime_http_ms',gen_seed['latency_ms'],1),metric('H.generated_cache_http_ms',gen_hit['latency_ms'],1),
                        metric('H.generated_cache_exact_hit',int(gen_hit['body'].get('cache',{}).get('kind')=='exact'),1),
                        metric('H.generated_observed_latency_saved_ms',gen_seed['latency_ms']-gen_hit['latency_ms'],1)])
        # Source moves and deletion measured after original answer; no item fallback exists.
        doc=dataset['documents'][0];sid=source_map[doc['id']];q='Where is my Aadhaar card?'
        seeded=api.ask('freshness-before-move',q)
        moved=api.location({'action':'attach','kind':'source','id':sid,'locationId':paths['Living room > Cabinet']})
        after=api.ask('freshness-after-move',q);after['correct']=found_paths(after)==['Living room > Cabinet'];after['cache_invalidated']=not after['body'].get('cache',{}).get('hit',False)
        api.location({'action':'deleteSource','id':sid})
        deleted=api.ask('freshness-after-delete',q,generation=True);deleted['correct']=deleted['body'].get('confidence')=='insufficient' and not found_paths(deleted);deleted['cache_invalidated']=not deleted['body'].get('cache',{}).get('hit',False)
        metrics.append(metric('E.move_freshness',int(after['correct']),1));metrics.append(metric('E.delete_freshness',int(deleted['correct']),1))
        metrics.append(metric('H.move_delete_invalidation',rate([after,deleted],'cache_invalidated'),2))
        # Duplicate source names at different paths: list both, refuse arbitrary single location.
        dup_sid,dup_ready=api.upload('PAN card','Permanent account number TESTP0001A.',paths['Study > Desk > Top drawer'])
        duplicate=api.ask('duplicate-pan','Where is my PAN card?',extra={'bypassCache':True})
        duplicate['correct']=set(found_paths(duplicate))=={'Living room > Cabinet','Study > Desk > Top drawer'} and duplicate['body'].get('confidence')=='conflicting'
        metrics.append(metric('E.duplicate_location_handling',int(duplicate['correct']),1))
        # Cache deliberately uses saved facts to isolate reuse from slow/variable generation.
        item=api.call('/api/atlas?householdId='+api.hid,{'action':'addItem','name':'Evaluation appliance','serialNumber':'DEMO-CACHE-0001','model':'DEMO-MODEL-01','make':'Fictional brand'})['body']['item']
        api.location({'action':'attach','kind':'item','id':item['id'],'locationId':paths['Study > Desk > Top drawer']})
        config['cache_expected_item']={'id':item['id'],'value':'DEMO-CACHE-0001','locationPath':'Study > Desk > Top drawer'}
        api.clear();base='What is my Evaluation appliance serial number?'
        warm=api.ask('cache-warmup',base);warm['group']='H'
        exact=[]
        for i in range(5):
            row=api.ask(f'cache-exact-{i+1}',base);row.update(group='H',correct=row['body'].get('cache',{}).get('kind')=='exact');exact.append(row)
        variants=['Show me the serial number of my Evaluation appliance','Tell me my Evaluation appliance serial number','What is the serial number of my evaluation appliance?',
                  'Give me my Evaluation appliance serial number','Please show the serial number of my Evaluation appliance','What is my Evaluation applliance serial number?',
                  'Show my Evaluation appliance serial number','Tell me the serial number for my Evaluation appliance','What is my Evaluation appliance serial no?',
                  'What is my Evaluation appliance identification number?']
        semantic=[]
        for i,v in enumerate(variants):
            row=api.ask(f'cache-variant-{i+1}',v,generation=True);row.update(group='H',correct=row['body'].get('cache',{}).get('hit',False),semantic_hit=row['body'].get('cache',{}).get('kind')=='semantic');semantic.append(row)
        # Inspect production cache through authenticated private API, avoid full generation on misses.
        near=['What is my Evaluation appliance model number?','What is my Evaluation appliance brand?',
          'What is my Evaluation appliance warranty date?','What is my Washing machine serial number?',
          'What is my Evaluation appliance photo serial number?','What is my Evaluation appliance serial number in Kitchen?',
          'What is my Evaluation appliance serial number in Bedroom?','What is my Evaluation appliance serial number DEMO-CACHE-0002?',
          'Where is my Evaluation appliance?','What is my Evaluation appliance purchase date?']
        near_rows=[]
        for i,v in enumerate(near):
            result=api.call('/cache/lookup',{'householdId':api.hid,'actorId':api.actor,'question':v,'scopeKey':json.dumps({'itemId':None,'roomId':None},separators=(',',':'))},worker=True)
            result.update(id=f'cache-near-miss-{i+1}',question=v,group='H',false_hit=result['body'].get('hit',False));api.rows.append(result);near_rows.append(result)
        bypass=[]
        for i in range(5):
            row=api.ask(f'cache-bypass-{i+1}',base,extra={'bypassCache':True});row['group']='H';bypass.append(row)
        api.location({'action':'attach','kind':'item','id':item['id'],'locationId':paths['Kitchen > Cabinet']})
        moved_item=api.ask('cache-item-after-move',base);moved_item.update(group='H',correct=found_paths(moved_item)==['Kitchen > Cabinet'] and not moved_item['body'].get('cache',{}).get('hit',False))
        api.sql('DELETE FROM items WHERE household_id=%s AND id=%s',(api.hid,item['id']))
        deleted_item=api.ask('cache-item-after-delete',base,generation=True);deleted_item.update(group='H',correct=deleted_item['body'].get('confidence')=='insufficient' and not deleted_item['body'].get('cache',{}).get('hit',False))
        metrics.extend([metric('H.exact_hit_rate',rate(exact,'correct'),len(exact)),metric('H.variant_hit_rate',rate(semantic,'correct'),len(semantic)),
          metric('H.semantic_hit_rate',rate(semantic,'semantic_hit'),len(semantic)),metric('H.near_miss_false_hit_rate',rate(near_rows,'false_hit'),len(near_rows)),
          metric('H.item_move_delete_freshness',rate([moved_item,deleted_item],'correct'),2),
          metric('H.warmup_http_ms',warm['latency_ms'],1),metric('H.exact_http_mean_ms',statistics.mean(r['latency_ms'] for r in exact),len(exact)),
          metric('H.bypass_http_mean_ms',statistics.mean(r['latency_ms'] for r in bypass),len(bypass)),
          metric('H.exact_latency_saved_ms',statistics.mean(r['latency_ms'] for r in bypass)-statistics.mean(r['latency_ms'] for r in exact),min(len(bypass),len(exact))),
          metric('H.llm_calls_saved',None,len(exact)+len(semantic),reason='Production API has no generation/verification call counter. Saved-fact exact/cache tests take a path without LLM generation; no invented call counts.'),
          metric('H.semantic_http_mean_ms',statistics.mean(r['latency_ms'] for r in semantic),len(semantic))])
        config['cache_metrics_runtime']=api.call('/api/cache?householdId='+api.hid,method='GET')['body']
        config['observed_worker_health']=requests.get('http://127.0.0.1:8001/health',timeout=10).json()
        config['source_mapping']={d['key']:source_map[d['id']] for d in dataset['documents']}
        config['qa_cache_namespace']=cache_key('homeatlas-no-answer-replay',{'fixture':api.hid},args.phase,args.run,MAIN)
        for name in ['AUROC','Brier','ECE','reliability_table']:
            metrics.append(metric('I.'+name,None,len([r for r in api.rows if 'confidence'in r]),reason='Application emits categorical confidence (supported/conflicting/insufficient), not a numeric correctness probability. Calibration cannot be computed honestly.'))
    finally:api.cleanup()
    for row in api.rows:row['run_id']=f'{args.phase}-run-{args.run:02}'
    result=make_result('homeatlas-agent',args.phase,args.run,metrics,api.rows,config,MAIN)
    result['models']['observed_runtime']=config.get('observed_worker_health',{}).get('models',{})
    write_result(args.output,result);print(json.dumps({'saved':str(args.output),'phase':args.phase,'run':args.run,'metrics':len(metrics),'rows':len(api.rows)}),flush=True)

def measure_generation_counter(args):
    """Small in-process app-path experiment, counting actual Ollama HTTP calls.

    Complements authenticated API timings; does not claim production telemetry.
    No fake model or cached model response is substituted.
    """
    import importlib
    sys.path.insert(0,str(MAIN))
    module=importlib.import_module('worker.models')
    from worker.config import settings
    from worker.retrieval import query_records
    from worker.search.cache import lookup,store
    api=API();calls=[];original=module.urlopen
    def observed(request,*a,**kw):
        try:payload=json.loads(request.data)
        except (TypeError,ValueError,AttributeError):payload={}
        start=time.monotonic()
        row={'stage':'ollama_request','model':payload.get('model'),'http_attempt':True}
        calls.append(row)
        try:
            response=original(request,*a,**kw)
            row['http_success']=True
            return response
        except Exception:
            row['http_success']=False;raise
        finally:row['http_setup_ms']=(time.monotonic()-start)*1000
    module.urlopen=observed
    measurements=[]
    try:
        api.start(args.phase,args.run)
        room=api.location({'action':'create','type':'room','parentId':api.hid,'name':'Kitchen'})
        cabinet=api.location({'action':'create','type':'zone','parentId':room,'name':'Cabinet'})
        doc=next(d for d in json.loads((HERE/'scenarios.json').read_text())['documents'] if d['key']=='fridge')
        sid,_=api.upload(doc['title'],doc['text'],cabinet)
        engine=module.LocalModels(settings)
        question='When does the fridge warranty expire?'
        for id,bypass in [('cache-generated-counter-prime',False),('cache-generated-counter-exact',False),('cache-generated-counter-bypass',True)]:
            before=len(calls);wait_start=time.monotonic()
            with shared_generation_slot():
                lock_wait=(time.monotonic()-wait_start)*1000;start=time.monotonic()
                cached=lookup(api.hid,api.actor,question,'measured-ollama-calls',settings,engine,bypass)
                if cached['hit']:answer=cached['answer']
                else:
                    answer=query_records(api.hid,api.actor,question,cfg=settings,engine=engine)
                    for cite in answer.get('citations',[]):
                        cite['locationPath']='Kitchen > Cabinet'
                    if not bypass:store(api.hid,api.actor,question,'measured-ollama-calls',cached['dataVersion'],answer,(time.monotonic()-start)*1000,settings,engine)
                elapsed=(time.monotonic()-start)*1000
            delta=calls[before:]
            measurements.append({'id':id,'run_id':f'{args.phase}-run-{args.run:02}','group':'H','transport':'in-process production query_records + versioned cache interface',
                                 'cache_hit':cached['hit'],'cache_kind':cached.get('kind'),'bypass':bypass,'latency_ms':elapsed,'generation_lock_wait_ms':lock_wait,
                                 'ollama_http_attempts':len(delta),'ollama_http_successes':sum(bool(c.get('http_success')) for c in delta),
                                 'calls':delta,'answer':answer,'expected_facts':['May','2028'],'correct':all(contains_fact(answer['answer'],x) for x in ['May','2028']),
                                 'source_fixture_id':doc['id'],'source_id':sid,'numeric_confidence':None})
            print('completed '+id,flush=True)
        payload=json.loads(args.output.read_text());result=next(r for r in payload['runs'] if r['phase']==args.phase and r['run']==args.run)
        for row in measurements:result['per_question'].append(row)
        prime,hit,bypass=measurements
        result['metrics']=[m for m in result['metrics'] if m['metric']!='H.llm_calls_saved']
        result['metrics'].extend([
          metric('H.llm_http_calls_saved',bypass['ollama_http_attempts']-hit['ollama_http_attempts'],1,scope='One actual generated-answer pair; includes generation and verifier HTTP calls; not inferred from latency.'),
          metric('H.generated_inprocess_cache_hit',int(hit['cache_hit']),1),
          metric('H.generated_inprocess_bypass_llm_calls',bypass['ollama_http_attempts'],1),
          metric('H.generated_inprocess_cached_llm_calls',hit['ollama_http_attempts'],1),
          metric('H.generated_inprocess_latency_saved_ms',bypass['latency_ms']-hit['latency_ms'],1),
          metric('H.generated_inprocess_fact_presence',sum(r['correct'] for r in measurements)/len(measurements),len(measurements))])
        result['config']['generation_count_method']='Evaluation-only wrapper observes actual worker.models.urlopen requests in production query_records and cache code. Separate disposable fixture; no LLM response replay. Prime/exact/bypass order fixed; includes embedding warmup on prime.'
        result['models']['inprocess_observed']=dict(engine.status)
        write_result(args.output,result)
    finally:module.urlopen=original;api.cleanup()

if __name__=='__main__':
    parser=argument_parser(__doc__);parser.add_argument('--counter-only',action='store_true')
    args=parser.parse_args()
    if not args.counter_only:evaluate(args)
    measure_generation_counter(args)
