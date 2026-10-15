"""Shared, bounded source images for generation and independent evidence review."""
import base64
import io
import re
from PIL import Image
from .pictures import oriented_rgb


def encoded(picture,limit=2048):
    picture=oriented_rgb(picture)
    picture.thumbnail((limit,limit))
    stream=io.BytesIO();picture.save(stream,format='JPEG',quality=95)
    return base64.b64encode(stream.getvalue()).decode()


VISUAL_TERMS = re.compile(r'\b(chart|diagram|figure|graph|plot\w*|trend\w*|illustration|photo\w*|picture|image|table)\b', re.I)


def needs_image(related, question=''):
    """Keep visual/OCR evidence; native prose previews add no independent facts."""
    if VISUAL_TERMS.search(question):
        return True
    for row in related:
        meta = row.get('metadata') or {}
        if (meta.get('extractor') != 'pymupdf' or meta.get('requires_visual_evidence') or
                meta.get('visual_anchor') or meta.get('ocr') or VISUAL_TERMS.search(row.get('text', ''))):
            return True
        # Older indexes lack the page's graphics marker. Short native blocks may
        # be headings above an unparsed image, so retain those previews.
        if 'requires_visual_evidence' not in meta and len(row.get('text', '')) < 200:
            return True
    return False


def attachments(evidence,cfg,question=''):
    images=[];labels=[];seen=set();crops=0
    for row in evidence:
        path=row.get('image_path')
        if not path or path in seen or len(seen)>=4:continue
        related=[e for e in evidence if e.get('image_path')==path]
        if not needs_image(related,question):continue
        seen.add(path)
        indices=[e['index'] for e in related]
        with Image.open(cfg.private_path(path)) as source:
            original=oriented_rgb(source)
            images.append(encoded(original))
            labels.append(f'Attached source image {len(images)} belongs to indices {indices}.')
            # Preserve small identifiers/labels at native resolution in a second detail view.
            detail=next((e for e in related if e.get('bbox') and any(c.isdigit() for c in e.get('text',''))),None)
            if detail and crops<2:
                meta=detail.get('metadata') or {};box=detail['bbox']
                sx=original.width/max(1,meta.get('width',original.width))
                sy=original.height/max(1,meta.get('height',original.height))
                bounds=(max(0,int(box[0]*sx)-20),max(0,int(box[1]*sy)-20),
                        min(original.width,int(box[2]*sx)+20),min(original.height,int(box[3]*sy)+20))
                if bounds[2]>bounds[0] and bounds[3]>bounds[1] and (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<.8*original.width*original.height:
                    images.append(encoded(original.crop(bounds),1600));crops+=1
                    labels.append(f'Attached source image {len(images)} is a detail crop of the SAME source, index {detail["index"]}.')
    return images,'\n'.join(labels)
