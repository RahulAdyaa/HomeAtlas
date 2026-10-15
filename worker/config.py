from dataclasses import dataclass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env.local', override=False)
    load_dotenv(ROOT / '.env', override=False)
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://localhost:54329/homeatlas')
    worker_key: str = os.getenv('WORKER_KEY', '')
    storage: Path = (ROOT / os.getenv('STORAGE_ROOT', os.getenv('STORAGE_DIR', '.data/storage'))).resolve()
    model_dir: Path = Path(os.getenv('MODEL_DIR', str(ROOT / 'data' / 'models'))).resolve()
    text_model: str = os.getenv('TEXT_EMBEDDING_MODEL', 'intfloat/multilingual-e5-small')
    text_revision: str = os.getenv('TEXT_EMBEDDING_REVISION', '614241f622f53c4eeff9890bdc4f31cfecc418b3')
    reranker_model: str = os.getenv('RERANKER_MODEL', 'BAAI/bge-reranker-base')
    reranker_revision: str = os.getenv('RERANKER_REVISION', '2cfc18c9415c912f9d8155881c133215df768a70')
    image_model: str = os.getenv('IMAGE_EMBEDDING_MODEL', 'google/siglip2-base-patch16-224')
    image_revision: str = os.getenv('IMAGE_EMBEDDING_REVISION', '75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2')
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    generation_model: str = os.getenv('GENERATION_MODEL', 'qwen3-vl:4b-instruct')
    ocr_backend: str = os.getenv('OCR_BACKEND', 'tesseract')
    ocr_languages: str = os.getenv('OCR_LANGUAGES', 'eng+hin')
    max_bytes: int = int(os.getenv('MAX_UPLOAD_BYTES', str(50 * 1024 * 1024)))
    max_duration: int = int(os.getenv('MAX_MEDIA_SECONDS', '900'))
    max_pdf_pages: int = int(os.getenv('MAX_PDF_PAGES', '250'))
    lease_seconds: int = 180
    max_attempts: int = 3

    def private_path(self, path: str) -> Path:
        result = Path(path).resolve(strict=True)
        if not result.is_relative_to(self.storage) or not result.is_file():
            raise ValueError('File is outside private storage')
        return result


settings = Settings()
