"""Shared, bounded source images for generation and independent evidence review."""
import base64
import io
from PIL import Image
from .pictures import oriented_rgb


def encoded(picture,limit=2048):
    picture=oriented_rgb(picture)
    picture.thumbnail((limit,limit))
    stream=io.BytesIO();picture.save(stream,format='JPEG',quality=95)
    return base64.b64encode(stream.getvalue()).decode()


def attachments(evidence,cfg):
    images=[];labels=[];seen=set();crops=0
    for row in evidence:
        path=row.get('image_path')
        if not path or path in seen or len(seen)>=4:continue
        seen.add(path)
        related=[e for e in evidence if e.get('image_path')==path]
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
