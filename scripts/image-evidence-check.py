"""Deterministic OCR before/after check with fictional labels and known gold fields."""
import io,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fitz,pytesseract
from PIL import Image,ImageDraw,ImageFont
from worker.ingestion import extract
root=Path('.data/image-evidence-qa');root.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype(next(p for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),36)
image=Image.new('RGB',(1200,650),'white');draw=ImageDraw.Draw(image)
for i,text in enumerate(['FICTIONAL HOUSEHOLD RECORD','Aadhaar card','Serial number: DEMO-00001234','Stored in Study desk drawer']):draw.text((70,65+i*110),text,font=font,fill='black')
image.save(root/'card.png');image.rotate(90,expand=True).save(root/'rotated-card.png');image.resize((480,260)).save(root/'small-card.png')
stream=io.BytesIO();image.save(stream,format='PNG');pdf=fitz.open();page=pdf.new_page(width=650,height=500);page.insert_text((30,35),'Household identity records - uploaded card',fontsize=15);page.insert_image(fitz.Rect(20,65,630,420),stream=stream.getvalue());pdf.save(root/'mixed.pdf');pdf.close()
rows=[]
for name,mime in [('card.png','image/png'),('rotated-card.png','image/png'),('small-card.png','image/png'),('mixed.pdf','application/pdf')]:
 path=root/name;t=time.perf_counter()
 if mime=='application/pdf':
  with fitz.open(path) as doc:baseline=' '.join(p.get_text() for p in doc)
 else:
  with Image.open(path) as im:baseline=pytesseract.image_to_string(im,config='--psm 6')
 oldms=(time.perf_counter()-t)*1000;t=time.perf_counter();chunks=extract(path,mime,root/(name+'-derived'));text='\n'.join(c.text for c in chunks)
 rows.append({'case':name,'old_exact_identifier':'DEMO-00001234' in baseline,'new_exact_identifier':'DEMO-00001234' in text,'old_ms':oldms,'new_ms':(time.perf_counter()-t)*1000,'label_and_value_same_chunk':any('Aadhaar' in c.text and 'DEMO-00001234' in c.text for c in chunks)})
Path('evaluation/image-ocr-results.json').write_text(json.dumps({'fictional_only':True,'cases':rows},indent=2))
lines=['# Image evidence regression results','','Four fictional fixtures; this is not a customer-data accuracy estimate. Exact identifier matching uses the authored string, without numeric correction.','', '| Case | Previous exact field | Updated exact field | Label + value together | Old OCR ms | Updated extraction ms |','|---|---|---|---|---:|---:|']
for r in rows:lines.append(f'| {r["case"]} | {r["old_exact_identifier"]} | {r["new_exact_identifier"]} | {r["label_and_value_same_chunk"]} | {r["old_ms"]:.0f} | {r["new_ms"]:.0f} |')
lines+=['','Previous means original PSM-6 OCR for images and native-text extraction for the mixed PDF. Updated time includes language selection, bounded layout/orientation passes and context grouping. Better recovery costs extra processing time.','', 'Automated tests also cover source coordinates, visual-only text retrieval, citable image anchors, and retaining immutable originals. Real upload-to-answer results are recorded separately by `scripts/image-upload-qa.mjs`.','', 'Limits: tiny text, blur, handwriting, perspective distortion and complex charts can still fail. Visual similarity only selects candidates. Generated visual claims require a separate image review; low-confidence identifier answers abstain. Existing uploads need reprocessing to obtain the improved OCR index.']
Path('evaluation/IMAGE_PIPELINE_REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(rows))
