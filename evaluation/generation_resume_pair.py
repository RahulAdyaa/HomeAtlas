"""Resume in-flight same-run evidence, finalize reference metrics, then execute independent run2."""
import os,time,json,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent;sys.path.insert(0,str(E))
from protocol import questions,cache_key,digest,app_fingerprint
from generation_eval import Engine,metrics_for
pid=int(sys.argv[1])
while True:
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(5)
runtime=E/'runtime/generation/questions'
engine=Engine('baseline',1);corpuskey=digest([app_fingerprint()['app_source_fingerprint'],engine.text_identity,engine.image_identity]);corpus=json.loads((E/'runtime/generation/corpora'/(corpuskey+'.json')).read_text())
for q in questions('pdf'):
 old=runtime/(cache_key('generation-question',q,'baseline',1)+'.json');new=runtime/(cache_key('main-generation-question',q,'baseline',1)+'.json')
 if old.exists() and not new.exists():
  row=json.loads(old.read_text());row['inference_pass']='main'
  # Additional deterministic citation page annotation metric; never changes model answers.
  citations=row['result'].get('citations',[]);gold=set(row['relevant_ids']);pages=set(q.get('source_pages',[]))
  row['metrics']=metrics_for(q,row['result'],[],corpus)
  new.write_text(json.dumps(row,indent=2))
for run in [1,2]:
 subprocess.run([sys.executable,str(E/'generation_eval.py'),'--phase','baseline','--run',str(run),'--output',str(E/'results/generation-agent.json')],check=True)
