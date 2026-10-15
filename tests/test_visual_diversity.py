"""Visual candidates represent source pages, not each duplicate OCR line."""
from worker.search.visual import search

class Engine:
    image_identity = 'vision-test'
    def embed_image_space(self, **kwargs): return [1., 0.]

def picture(key, path, text, **metadata):
    return dict(id=key, source_id='source', version_id='version', page=1,
                image_path=path, text=text, metadata=metadata,
                image_embedding=[1., 0.], image_embedding_model='vision-test')

def test_visual_deduplicates_before_limit_and_prefers_context():
    rows = [picture(f'line-{i}', 'page-a.png', 'label') for i in range(35)]
    rows += [picture('context', 'page-a.png', 'Full labels and values.', ocr_context=True),
             picture('other-page', 'page-b.png', 'Another page.')]
    hits = search('labels', rows, Engine(), 2)
    assert [h.id for h in hits] == ['context', 'other-page']

def test_visual_dedup_does_not_merge_distinct_sources_or_versions():
    a = picture('a', 'page.png', 'same text')
    b = dict(a, id='b', source_id='other-source')
    c = dict(a, id='c', version_id='other-version')
    assert len(search('labels', [a,b,c], Engine())) == 3
