import hashlib
import io
from worker.jobs import sha256_stream

def test_stream_hash_is_bounded_and_does_not_require_python311(monkeypatch):
    data=b'fictional household text\x00' * 100000
    class Bounded(io.BytesIO):
        def read(self,size=-1):
            assert 0<size<=1024*1024
            return super().read(size)
    monkeypatch.delattr(hashlib,'file_digest',raising=False)
    assert sha256_stream(Bounded(data))==hashlib.sha256(data).hexdigest()

def test_empty_file_hash():
    assert sha256_stream(io.BytesIO())==hashlib.sha256(b'').hexdigest()
