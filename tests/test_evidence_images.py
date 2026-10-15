"""Image selection retains actual visual evidence without retransmitting text previews."""
from types import SimpleNamespace
from PIL import Image
from worker.vision_assets import attachments

TEXT = ('The appliance manual describes regular cleaning and filter replacement. '
        'Disconnect power before cleaning. Replace the filter every six months. ')*3

def record(path, **extra):
    return dict(index=0,text=TEXT,image_path=str(path),metadata={'extractor':'pymupdf'},**extra)

def test_reliable_native_text_does_not_attach_page_preview(tmp_path):
    path=tmp_path/'native.png'; Image.new('RGB',(20,20),'white').save(path)
    images,_=attachments([record(path)],SimpleNamespace(private_path=lambda p:p))
    assert images == []

def test_visual_chart_diagram_and_scanned_evidence_remain_attached(tmp_path):
    cfg=SimpleNamespace(private_path=lambda p:p)
    for kind in ['chart','diagram','scanned','mixed','short-heading','visual-metadata']:
        path=tmp_path/(kind+'.png');Image.new('RGB',(20,20),'white').save(path)
        row=record(path)
        if kind=='chart':row['text']='Chart: monthly water usage. '+TEXT
        elif kind=='diagram':row['text']='Figure: filter arrangement. '+TEXT
        elif kind=='scanned':row['metadata']={'ocr':'tesseract'}
        elif kind=='mixed':row['metadata']={'extractor':'mixed-pdf-ocr'}
        elif kind=='short-heading':row['text']='Installation diagram'
        else:row['metadata']['requires_visual_evidence']=True
        assert len(attachments([row],cfg)[0])==1,kind

def test_visual_query_preserves_even_unlabelled_native_graph(tmp_path):
    path=tmp_path/'native.png';Image.new('RGB',(20,20),'white').save(path)
    assert attachments([record(path)],SimpleNamespace(private_path=lambda p:p),question='Compare the plotted trends')[0]
