"""Reproducible synthetic source-page retrieval comparison for PDF cleanup.

Run from the repository root with worker/.venv/bin/python evaluation/answer_cleanup_retrieval.py.
This is a fixed 20-question subset and does not replace the full frozen RAG report.
"""
import json
import statistics
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import worker.ingestion as ingestion
from worker.models import models
from worker.retrieval import rank_candidates
from worker.search.common import CONFIG
from evaluation.retrieval_metrics import metrics


def corpus(directory:Path,clean:bool):
    original_clean,original_margins=ingestion.clean_pdf_text,ingestion.repeated_pdf_margins
    if not clean:
        ingestion.clean_pdf_text=lambda text, margins=None:text
        ingestion.repeated_pdf_margins=lambda document:set()
    try:
        rows=[]
        for pdf in sorted((ROOT/'evaluation/fixtures').glob('*.pdf')):
            if pdf.stem=='scanned':continue
            folder=directory/pdf.stem;folder.mkdir(parents=True,exist_ok=True)
            for index,chunk in enumerate(ingestion.extract_pdf(pdf,folder)):
                rows.append({'id':f'{pdf.name}:{chunk.page}:{index}','source_id':pdf.name,
                             'version_id':pdf.name,'title':pdf.name,'text':chunk.text,
                             'page':chunk.page,'metadata':chunk.metadata,'location_path':''})
        vectors=models.embed_text([row['text'] for row in rows])
        if not vectors:raise RuntimeError('Pinned multilingual embedding model unavailable')
        for row,vector in zip(rows,vectors):row.update(embedding=vector,embedding_model=models.text_identity)
        return rows
    finally:
        ingestion.clean_pdf_text,ingestion.repeated_pdf_margins=original_clean,original_margins


def main():
    questions=json.loads((ROOT/'evaluation/testset.json').read_text())['questions']
    selected=[]
    for modality in ('text','table','image','chart'):
        selected.extend([q for q in questions if q['modality']==modality and not q['unanswerable']][:5])
    original_visual=CONFIG['visual']['enabled'];CONFIG['visual']['enabled']=False
    try:
        with TemporaryDirectory(prefix='homeatlas-cleanup-eval-') as temp:
            base=corpus(Path(temp)/'before',False);after=corpus(Path(temp)/'after',True)
            runs={}
            for label,documents in (('before',base),('after',after)):
                per=[]
                for q in selected:
                    candidates=rank_candidates(q['question'],documents,models)
                    ranked=[f"{row['source_id']}:{row['page']}" for row in candidates]
                    relevant=[f"{q['source_document']}:{page}" for page in q['source_pages']]
                    per.append({'id':q['id'],'ranked_source_pages':ranked,'relevant_source_pages':relevant,
                                'metrics':metrics(ranked,relevant,5)})
                runs[label]={'n':len(per),'recall_at_5':statistics.mean(r['metrics']['recall'] for r in per),
                             'mrr_at_5':statistics.mean(r['metrics']['mrr'] for r in per),'per_question':per}
    finally:
        CONFIG['visual']['enabled']=original_visual
    output={'scope':'20 fixed synthetic answerable questions, 5 each text/table/image/chart; source-page relevance; in-process three text channels with pinned multilingual embeddings; visual channel disabled identically before/after; no user data or live DB',
            'before':runs['before'],'after':runs['after']}
    destination=ROOT/'evaluation/results/answer-cleanup-retrieval.json'
    destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({label:{key:value for key,value in runs[label].items() if key!='per_question'} for label in runs},indent=2))


if __name__=='__main__':main()
