"""Original CC0 fixtures; ground truth authored independently of extraction."""
from pathlib import Path
import json, io, random
import fitz
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n): return ImageFont.truetype(FONT,n)
def raster(lines, size=(1200,1500)):
 im=Image.new('RGB',size,'white'); d=ImageDraw.Draw(im)
 for i,t in enumerate(lines): d.text((70,90+i*100),t,font=font(32),fill='black')
 return im
def png(im):
 b=io.BytesIO(); im.save(b,format='PNG');return b.getvalue()
def build():
 random.seed(741); (ROOT/'fixtures').mkdir(exist_ok=True)
 questions=[]; manifests=[]
 def q(mod,i,question,answer,pages,terms,typ='factual',region=None):
  questions.append(dict(id=f'{mod}-{i:02}',modality=mod,question=question,reference_answer=answer,source_document=f'{mod}.pdf',source_pages=pages,evidence_terms=terms,type=typ,unanswerable=not pages,source_regions=region or [],reference_chunks=[]))
 for mod in ['text','table','image','chart','scanned']:
  doc=fitz.open(); facts=[]; texts=[]; tables=[]; figures=[]
  for n in range(1,5):
   p=doc.new_page(width=600,height=750)
   title=f'HomeAtlas evaluation: {mod} record {n}'
   if mod=='text':
    a=f'Unit T{n} has a warranty of {12+n*6} months.'; b=f'Unit T{n} requires a service inspection every {n+2} months.'
    lines=[title,a,b,f'The service provider for unit T{n} is Cedar Workshop.', 'This fictional record is an evaluation fixture, not advice for a real product.']
    p.insert_textbox(fitz.Rect(45,45,550,700),'\n\n'.join(lines),fontsize=14)
    q(mod,2*n-1,f'How long is the warranty for unit T{n}?',a,[n],[str(12+n*6),'months'])
    q(mod,2*n,f'How often does unit T{n} need a service inspection?',b,[n],[str(n+2),'months'])
   elif mod=='table':
    lines=[title,f'Costs below are monthly. Table {n} lists appliance modes.']
    p.insert_textbox(fitz.Rect(40,30,560,110),'\n'.join(lines),fontsize=13)
    cells=[['Mode','Power W','Cost USD'],['Eco',str(20+n),str(3+n)],['Normal',str(40+n),str(6+n)],['Boost',str(70+n),str(10+n)]]
    for r,row in enumerate(cells):
     for c,val in enumerate(row):
      box=fitz.Rect(45+c*165,150+r*65,210+c*165,215+r*65);p.draw_rect(box);p.insert_text((box.x0+12,box.y0+35),val,fontsize=16)
    tables.append({'page':n,'cells':cells,'bbox':[45,150,540,410]})
    lines+=[' '.join(row) for row in cells]
    a=f'Boost power is {70+n} W.';b=f'Normal monthly cost is {6+n} USD.'
    q(mod,2*n-1,f'In table {n}, what is the Boost power in watts?',a,[n],['Boost',str(70+n)])
    q(mod,2*n,f'In table {n}, what is the monthly Normal cost in USD?',b,[n],['Normal',str(6+n)],'cross-modal')
   elif mod=='image':
    p.insert_text((40,45),title,fontsize=14)
    labels=['INLET','MESH','HEPA','FAN']; im=Image.new('RGB',(1100,600),'white');d=ImageDraw.Draw(im)
    colors=['lightblue','gold','lightgreen','salmon']
    for j,label in enumerate(labels):
     x=35+j*265;d.rectangle((x,160,x+220,300),fill=colors[j],outline='black',width=4);d.text((x+25,205),label,font=font(34),fill='black')
     if j<3: d.line((x+220,230,x+265,230),fill='black',width=5);d.polygon([(x+260,220),(x+265,230),(x+260,240)],fill='black')
    d.text((50,380),f'Diagram {n}: Filter cartridge H{n}00',font=font(40),fill='black');d.text((50,450),f'Blue inlet; fan speed {n+1} levels',font=font(36),fill='black')
    p.insert_image(fitz.Rect(35,130,565,420),stream=png(im));lines=[title]
    figures.append({'page':n,'bbox':[35,130,565,420],'description':f'Left-to-right flow: blue INLET, gold MESH, green HEPA, salmon FAN. Cartridge H{n}00. Fan has {n+1} speed levels.','facts':['INLET','MESH','HEPA','FAN',f'H{n}00',str(n+1)]})
    a=f'The cartridge is H{n}00.';b='The HEPA stage is immediately before the FAN.'
    q(mod,2*n-1,f'What cartridge identifier is shown in diagram {n}?',a,[n],[f'H{n}00'],region=[[35,130,565,420]])
    q(mod,2*n,f'In diagram {n}, which stage is immediately before the fan?',b,[n],['HEPA','FAN'],region=[[35,130,565,420]])
   elif mod=='chart':
    p.insert_text((40,45),title,fontsize=14);im=Image.new('RGB',(1100,700),'white');d=ImageDraw.Draw(im)
    d.text((40,15),f'Chart {n}: household energy',font=font(34),fill='black'); vals=[20+n*5,40+n*5,60+n*5]
    d.line((120,90,120,580,1020,580),fill='black',width=4)
    for v in range(0,101,20):
     y=580-v*4;d.text((45,y-15),str(v),font=font(26),fill='black');d.line((110,y,1020,y),fill='lightgray',width=1)
    for j,(month,v) in enumerate(zip(['Jan','Feb','Mar'],vals)):
     x=220+j*260;d.rectangle((x,580-v*4,x+100,580),fill='royalblue');d.text((x,540-v*4),str(v),font=font(28),fill='black');d.text((x,600),month,font=font(28),fill='black')
    d.text((25,65),'kWh',font=font(28),fill='black');d.text((770,30),'Blue = usage',font=font(28),fill='royalblue');d.text((450,650),'Month',font=font(28),fill='black')
    p.insert_image(fitz.Rect(30,120,570,465),stream=png(im));lines=[title]
    figures.append({'page':n,'bbox':[30,120,570,465],'description':f'Blue bars represent usage; x-axis Month (Jan, Feb, Mar), y-axis kWh. Values {vals}. Usage increases every month.','facts':list(map(str,vals))+['kWh','Month','usage']})
    a=f'March usage is {vals[2]} kWh.';b='Usage increases from January through March.'
    q(mod,2*n-1,f'What is March energy usage in chart {n}?',a,[n],[str(vals[2]),'kWh'],'numeric/chart-reading',[[30,120,570,465]])
    q(mod,2*n,f'What trend does chart {n} show from January to March?',b,[n],['increases'],'numeric/chart-reading',[[30,120,570,465]])
   else:
    a=f'Pump S{n} was inspected on 2026-0{n}-15.';b=f'Pump S{n} pressure was {n+2} bar.'
    lines=[title,a,b,f'Technician: Morgan {n}.','Next inspection: 2027.']
    im=raster(lines);p.insert_image(p.rect,stream=png(im))
    q(mod,2*n-1,f'When was pump S{n} inspected?',a,[n],[f'2026-0{n}-15'])
    q(mod,2*n,f'What was the recorded pressure for pump S{n}?',b,[n],[str(n+2),'bar'])
   texts.append({'page':n,'text':'\n'.join(lines)})
   facts.extend([a,b])
  if mod=='text':
   q(mod,9,'Give the warranty durations for units T1 and T4.','T1: 18 months; T4: 36 months.',[1,4],['18','36'],'multi-chunk')
   q(mod,10,'Summarize the service inspection intervals for all four T units.','T1: 3, T2: 4, T3: 5, T4: 6 months.',[1,2,3,4],['3','4','5','6'],'summary')
  elif mod=='table':
   q(mod,9,'Give Boost power in table 1 and table 4.','Table 1: 71 W; table 4: 74 W.',[1,4],['71','74'],'multi-chunk')
   q(mod,10,'What period applies to the Eco cost of 4 USD in table 1?','The Eco cost is 4 USD per month.',[1],['4','monthly'],'cross-modal')
  elif mod=='image':
   q(mod,9,'Give cartridge identifiers shown in diagrams 1 and 4.','H100 and H400.',[1,4],['H100','H400'],'multi-chunk')
   q(mod,10,'Summarize the airflow sequence in diagram 2.','INLET, MESH, HEPA, FAN.',[2],['INLET','MESH','HEPA','FAN'],'summary')
  elif mod=='chart':
   q(mod,9,'Give March usage in charts 1 and 4.','65 kWh and 80 kWh.',[1,4],['65','80'],'multi-chunk')
   q(mod,10,'What are the axis labels and legend of chart 2?','X-axis: Month; y-axis: kWh; blue represents usage.',[2],['Month','kWh','usage'],'numeric/chart-reading')
  else:
   q(mod,9,'Give recorded pressures for pumps S1 and S4.','S1: 3 bar; S4: 6 bar.',[1,4],['3','6','bar'],'multi-chunk')
   q(mod,10,'Summarize the inspection year and next inspection year for the pumps.','Inspected in 2026; next inspection in 2027.',[1,2,3,4],['2026','2027'],'summary')
  q(mod,11,f'What is the Wi-Fi password listed in the {mod} records?','Not found.',[],[],'unanswerable')
  q(mod,12,f'What serial number is shown on the purple emergency valve in the {mod} records?','Not found; no such valve is documented.',[],[],'unanswerable')
  out=ROOT/'fixtures'/f'{mod}.pdf';doc.save(out,garbage=4,deflate=True,no_new_id=True);doc.close()
  manifests.append({'id':mod,'file':str(out.relative_to(ROOT)),'pages':texts,'tables':tables,'figures':figures,'license':'CC0; original evaluation fixture'})
 (ROOT/'testset.json').write_text(json.dumps({'seed':741,'ground_truth':'Authored from fixture specifications, not app answers; scan render visually reviewed.', 'questions':questions},indent=2))
 (ROOT/'fixtures/manifest.json').write_text(json.dumps(manifests,indent=2))
 return questions,manifests
if __name__=='__main__': build()
