"""Original CC0 sample household records; deliberately fictional appliances."""
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]/'tests'/'fixtures'
ROOT.mkdir(parents=True,exist_ok=True)
def document(name,title,pages):
    d=fitz.open()
    for number,paragraphs in enumerate(pages,1):
        p=d.new_page(width=595,height=842)
        p.draw_rect(fitz.Rect(0,0,595,115),color=None,fill=(.91,.94,.86))
        p.insert_text((45,45),'HOMEATLAS  /  ORIGINAL SAMPLE RECORD',fontsize=9,color=(.35,.42,.29))
        p.insert_text((45,80),title,fontsize=21,fontname='tiro',color=(.2,.3,.18))
        y=160
        for heading,body in paragraphs:
            p.insert_text((45,y),heading,fontsize=14,fontname='hebo',color=(.2,.3,.18))
            rect=fitz.Rect(45,y+18,540,y+125)
            p.insert_textbox(rect,body,fontsize=12,lineheight=1.6)
            y+=155
        p.insert_text((45,800),f'Fictional sample. CC0. Not advice for a real appliance. | Page {number}',fontsize=9,color=(.45,.45,.4))
    d.save(ROOT/name)
document('AirOne-AP200-manual.pdf','AirOne AP-200 air purifier',[[('Know your appliance','Model: AirOne AP-200. This fictional example belongs in the bedroom.'),('Everyday care','Switch off and unplug the appliance before routine cleaning. Wipe the exterior with a dry cloth. For any electrical fault, contact a qualified professional.')],[('Replacement filter','The AirOne AP-200 uses the A200-HEPA replacement filter. Replace the A200-HEPA filter every 180 days under normal use. No other filter compatibility is specified in this manual.'),('Filter reminder reset','After fitting a new A200-HEPA filter and closing the cover, hold the filter button for 5 seconds to reset the reminder. This procedure applies only to the fictional AirOne AP-200.')]])
document('AirOne-purchase-receipt.pdf','Your AirOne purchase',[[('Receipt HA-2026-017','Item: AirOne AP-200 air purifier. Purchased on 12 February 2026. Serial number: HA200-DEMO-017. This receipt is an original fictional sample, not a real purchase.'),('Warranty record','The warranty for this sample AirOne AP-200 expires on 12 February 2028. Retain this receipt with the manual. No additional warranty exclusions or rights are stated here.')]])
p=fitz.open(ROOT/'AirOne-AP200-manual.pdf');p[1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(ROOT/'filter-page-photo.png')
print('Created 2 original sample PDFs and one scan for ingestion tests.')
