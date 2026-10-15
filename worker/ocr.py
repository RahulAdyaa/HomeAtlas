"""Bounded OCR passes. Coordinates always refer to the EXIF-oriented original image."""
import math
from PIL import Image, ImageOps
from .pictures import oriented_rgb


def original_box(box, angle, width, height, scale):
    x0,y0,x1,y1=box
    points=[]
    for x,y in [(x0,y0),(x1,y0),(x0,y1),(x1,y1)]:
        x,y=x/scale,y/scale
        if angle==90: x,y=width-y,x
        elif angle==180:x,y=width-x,height-y
        elif angle==270:x,y=y,height-x
        points.append((x,y))
    return [max(0,min(x for x,y in points)),max(0,min(y for x,y in points)),
            min(width,max(x for x,y in points)),min(height,max(y for x,y in points))]


def read(picture,languages='eng+hin'):
    import pytesseract
    available=set(pytesseract.get_languages(config=''))
    lang='+'.join(l for l in languages.split('+') if l in available)
    if not lang:raise ValueError('No configured OCR language pack is installed')
    original=oriented_rgb(picture)
    width,height=original.size
    scale=min(2.0,max(1.0,1000/max(1,min(width,height))),math.sqrt(6_000_000/max(1,width*height)))
    work=ImageOps.autocontrast(ImageOps.grayscale(original))
    if scale!=1:work=work.resize((max(1,round(width*scale)),max(1,round(height*scale))),Image.Resampling.LANCZOS)
    def run(angle,psm):
        image=work.rotate(angle,expand=True) if angle else work
        data=pytesseract.image_to_data(image,lang=lang,config=f'--psm {psm}',output_type=pytesseract.Output.DICT,timeout=25)
        good=[i for i,t in enumerate(data['text']) if str(t).strip() and float(data['conf'][i])>=30]
        # Reward readable characters and penalize low-confidence noise.
        score=sum(len(str(data['text'][i]))*max(0,float(data['conf'][i])-35)/65 for i in good)
        confidence=sum(float(data['conf'][i]) for i in good)/max(1,len(good))
        return score,confidence,good,data,angle,psm
    choices=[run(0,6),run(0,11)]
    best=max(choices,key=lambda c:c[0])
    if len(best[2])<4 or best[1]<75:
        choices.extend(run(angle,6) for angle in (90,180,270))
        best=max(choices,key=lambda c:c[0])
    _,confidence,good,data,angle,psm=best
    lines={}
    for i in good:
        lines.setdefault((data['block_num'][i],data['par_num'][i],data['line_num'][i]),[]).append(i)
    result=[]
    for indices in lines.values():
        box=[min(data['left'][i] for i in indices),min(data['top'][i] for i in indices),
             max(data['left'][i]+data['width'][i] for i in indices),max(data['top'][i]+data['height'][i] for i in indices)]
        result.append(dict(text=' '.join(str(data['text'][i]) for i in indices),bbox=original_box(box,angle,width,height,scale),
            metadata={'ocr':'tesseract','width':width,'height':height,'confidence':sum(float(data['conf'][i]) for i in indices)/len(indices),
                      'ocr_languages':lang,'ocr_rotation':angle,'ocr_psm':psm,'exif_oriented':True,'coordinates':'image-pixels'}))
    return result
