"""Synthetic image regressions. Identifiers are deliberately fictional."""
from dataclasses import replace
import io
from pathlib import Path
import uuid
import fitz
from PIL import Image, ImageDraw, ImageFont
from worker.config import Settings
from worker.ingestion import extract
from worker.retrieval import rank_candidates
from worker.ocr import original_box


def card():
    im=Image.new('RGB',(1200,650),'white');draw=ImageDraw.Draw(im)
    f=ImageFont.truetype(next(p for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),36)
    for i,text in enumerate(['FICTIONAL HOUSEHOLD RECORD','Aadhaar card','Serial number: DEMO-00001234','Stored in Study desk drawer']):
        draw.text((70,65+i*110),text,font=f,fill='black')
    return im


def test_rotated_card_preserves_identifier_and_source_coordinates(tmp_path):
    path=tmp_path/'rotated.png';card().rotate(90,expand=True).save(path)
    chunks=extract(path,'image/png',tmp_path/'derived')
    assert any('DEMO-00001234' in c.text and 'Aadhaar' in c.text for c in chunks)
    for c in chunks:
        assert 0<=c.bbox[0]<=c.bbox[2]<=650
        assert 0<=c.bbox[1]<=c.bbox[3]<=1200
    assert any(c.metadata.get('ocr_rotation') in (90,270) for c in chunks)


def test_label_and_value_remain_together_in_image_context(tmp_path):
    path=tmp_path/'card.png';card().save(path)
    chunks=extract(path,'image/png',tmp_path/'derived')
    context=next(c for c in chunks if c.metadata.get('ocr_context'))
    assert 'Aadhaar' in context.text and 'DEMO-00001234' in context.text
    assert len(chunks)>1 and all(c.image_path==str(path) for c in chunks)
    assert 'confidence' in context.metadata


def test_pdf_with_native_heading_still_extracts_embedded_image(tmp_path):
    buffer=io.BytesIO();card().save(buffer,format='PNG')
    pdf=fitz.open();page=pdf.new_page(width=650,height=500)
    page.insert_text((30,35),'Household identity records - uploaded card',fontsize=15)
    page.insert_image(fitz.Rect(20,65,630,420),stream=buffer.getvalue())
    path=tmp_path/'mixed.pdf';pdf.save(path);pdf.close()
    chunks=extract(path,'application/pdf',tmp_path/'derived')
    assert any('DEMO-00001234' in c.text for c in chunks)
    assert any(c.metadata.get('extractor')=='mixed-pdf-ocr' for c in chunks)
    assert all(c.page==1 and c.image_path for c in chunks)
    assert all(0<=c.bbox[0]<=c.bbox[2]<=650 and 0<=c.bbox[1]<=c.bbox[3]<=500 for c in chunks)


def test_textless_image_has_citable_visual_anchor(tmp_path):
    path=tmp_path/'blank.png';Image.new('RGB',(200,180),'white').save(path)
    c=extract(path,'image/png',tmp_path/'derived')[0]
    assert len(c.text)>=8 and c.metadata['visual_anchor'] and c.modality=='image'


def test_text_query_can_retrieve_visual_only_record():
    class Engine:
        text_identity='text';image_identity='vision'
        def embed_text(self,*args,**kwargs):return None
        def embed_image_space(self,*,text=None,image=None):
            assert text=='a blue storage box'
            return [1.,0.]
    record=dict(id=uuid.uuid4(),text='Visual source image. Inspect the attached original for evidence.',
                title='photo',image_path='/private/original.png',image_embedding=[1.,0.],image_embedding_model='vision')
    result=rank_candidates('a blue storage box',[record],Engine())
    assert result[0]['id']==record['id'] and result[0]['visual_match']


def test_inverse_rotated_box():
    assert original_box([10,20,30,40],90,100,200,1)==[60,10,80,30]


def test_uncertain_identifier_never_falls_back_to_confident_ocr_quote():
    from types import SimpleNamespace
    from worker.retrieval import answer_from_evidence
    class Engine:
        cfg=SimpleNamespace(image_model='vision')
        def generate(self,*args,**kwargs):return {'quotes':[{'index':0,'quote':'Serial number DEMO-00001234'}]}
    record=dict(id=uuid.uuid4(),source_id=uuid.uuid4(),version_id=uuid.uuid4(),title='fictional card',
                text='Serial number DEMO-00001234',image_path='/private/card.png',metadata={'confidence':40})
    result=answer_from_evidence('What is the serial number?',[record],Engine())
    assert result['confidence']=='insufficient' and not result['citations']


def test_visual_anchor_cannot_be_returned_as_an_answer():
    from types import SimpleNamespace
    from worker.retrieval import answer_from_evidence
    anchor='Visual source image. Inspect the attached original for evidence.'
    class Engine:
        cfg=SimpleNamespace(image_model='vision')
        def generate(self,*args,**kwargs):return {'quotes':[{'index':0,'quote':anchor}]}
    record=dict(text=anchor,image_path='/private/image.png',metadata={'visual_anchor':True})
    assert answer_from_evidence('What is in this image?',[record],Engine())['mode']=='abstention'


def test_transparent_text_is_composited_on_white_before_ocr(tmp_path):
    image=Image.new('RGBA',(1200,650),(0,0,0,0));draw=ImageDraw.Draw(image)
    f=ImageFont.truetype(next(p for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),36)
    for i,text in enumerate(['FICTIONAL HOUSEHOLD RECORD','Aadhaar card','Serial number: DEMO-00001234']):draw.text((70,65+i*110),text,font=f,fill=(0,0,0,255))
    path=tmp_path/'transparent.png';image.save(path)
    chunks=extract(path,'image/png',tmp_path/'derived')
    assert any('DEMO-00001234' in c.text for c in chunks)
