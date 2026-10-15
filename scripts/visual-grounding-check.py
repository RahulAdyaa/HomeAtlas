"""Real local vision and independent-review checks on authored CC0 diagram/chart PDFs."""
import json,sys,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from worker.config import settings
from worker.ingestion import extract
from worker.models import models
from worker.retrieval import answer_from_evidence
root=settings.storage/'visual-grounding-qa';root.mkdir(parents=True,exist_ok=True)
results=[]
for kind,question,required in [
 ('image','In diagram 1, which filter stage is immediately before the fan?',['HEPA']),
 ('chart','What is March energy usage in chart 1? Include its unit.',['65','kWh'])]:
 chunks=[c for c in extract(Path('evaluation/fixtures')/(kind+'.pdf'),'application/pdf',root/kind) if c.page==1]
 sid,vid=uuid.uuid4(),uuid.uuid4()
 evidence=[dict(id=uuid.uuid4(),source_id=sid,version_id=vid,title=kind+'.pdf',text=c.text,page=c.page,bbox=c.bbox,
                image_path=c.image_path,metadata=c.metadata,lexical_score=1) for c in chunks[:8]]
 reply=answer_from_evidence(question,evidence,models)
 assert reply['confidence']=='supported' and all(word.lower() in reply['answer'].lower() for word in required), 'Visual facts were not verified'
 assert reply['citations'] and all(any(c['text'] in e['text'] for e in evidence) for c in reply['citations'])
 results.append({'case':kind,'mode':reply['mode'],'expectedTermsPresent':True,'canonicalQuotes':True})
 print('Visual grounding passed:',kind,flush=True)
Path('evaluation/visual-grounding-results.json').write_text(json.dumps({'fictionalOnly':True,'checks':results},indent=2))
