"""Bounded real extraction. Originals and their source coordinates are never rewritten."""
from dataclasses import dataclass, field
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import fitz
from PIL import Image, ImageOps

from .config import Settings, settings


@dataclass
class ExtractedChunk:
    text: str
    modality: str = 'text'
    page: int | None = None
    bbox: list[float] | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    image_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def command(argv: list[str], timeout: int = 90) -> str:
    try:
        result = subprocess.run(argv, capture_output=True, check=True, timeout=timeout)
        return result.stdout.decode('utf-8', errors='replace')
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        # stderr can contain private source paths; do not leak it into logs or job errors.
        raise ValueError(f'{Path(argv[0]).name} processing failed; check the file and installed runtime') from exc


def validate_file(path: Path, mime: str, cfg: Settings = settings) -> None:
    if not path.is_file() or path.stat().st_size == 0 or path.stat().st_size > cfg.max_bytes:
        raise ValueError('File is empty or exceeds the upload size limit')
    with path.open('rb') as source:
        head = source.read(32)
    if mime == 'application/pdf':
        if not head.startswith(b'%PDF-'):
            raise ValueError('PDF signature does not match its file type')
    elif mime.startswith('image/'):
        try:
            with Image.open(path) as picture:
                if picture.width * picture.height > 40_000_000:
                    raise ValueError('Image exceeds the 40 megapixel limit')
                picture.verify()
        except Exception as exc:
            raise ValueError('Invalid or oversized image') from exc
    elif mime.startswith(('audio/', 'video/')):
        probe_media(path, cfg)
    elif mime in ('text/plain', 'text/markdown'):
        if b'\x00' in head:
            raise ValueError('Invalid text file')
    else:
        raise ValueError('Unsupported file type')


def ocr_image(picture: Image.Image, cfg: Settings = settings) -> list[ExtractedChunk]:
    picture = ImageOps.exif_transpose(picture).convert('RGB')
    if cfg.ocr_backend == 'paddleocr':
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            # Production optional extra: paddleocr==2.10.0, paddlepaddle==3.0.0.
            engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            result = engine.ocr(np.asarray(picture), cls=True)
            chunks = []
            for line in (result[0] or []):
                points, (text, confidence) = line
                xs, ys = zip(*points)
                chunks.append(ExtractedChunk(text, 'ocr', bbox=[min(xs), min(ys), max(xs), max(ys)],
                                             metadata={'ocr': 'paddleocr', 'confidence': float(confidence)}))
            return chunks
        except ImportError as exc:
            raise ValueError('PaddleOCR is not installed; install the production OCR extra or select tesseract') from exc
    if not shutil.which('tesseract'):
        raise ValueError('Tesseract OCR is not installed')
    import pytesseract
    data = pytesseract.image_to_data(picture, config='--psm 6', output_type=pytesseract.Output.DICT, timeout=90)
    lines: dict[tuple[int, int, int], list[int]] = {}
    for i, text in enumerate(data['text']):
        if str(text).strip() and float(data['conf'][i]) >= 20:
            lines.setdefault((data['block_num'][i], data['par_num'][i], data['line_num'][i]), []).append(i)
    result = []
    for indices in lines.values():
        x0 = min(data['left'][i] for i in indices)
        y0 = min(data['top'][i] for i in indices)
        x1 = max(data['left'][i] + data['width'][i] for i in indices)
        y1 = max(data['top'][i] + data['height'][i] for i in indices)
        result.append(ExtractedChunk(' '.join(data['text'][i] for i in indices), 'ocr', bbox=[x0, y0, x1, y1],
                                    metadata={'ocr': 'tesseract', 'width': picture.width, 'height': picture.height}))
    return result


def split_text(text: str, limit: int = 1200) -> list[str]:
    # Paragraph boundaries first; oversized paragraphs split on sentence/word boundaries.
    parts = []
    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        current = ''
        for word in words:
            if len(current) + len(word) + 1 > limit and current:
                parts.append(current)
                current = ''
            current = (current + ' ' + word).strip()
        if current:
            parts.append(current)
    return parts


def extract_pdf(path: Path, artifact_dir: Path, cfg: Settings = settings) -> list[ExtractedChunk]:
    chunks = []
    with fitz.open(path) as document:
        if document.is_encrypted:
            raise ValueError('Password-protected PDFs cannot be indexed')
        if len(document) > cfg.max_pdf_pages:
            raise ValueError('PDF exceeds the page limit')
        for index, page in enumerate(document):
            blocks = page.get_text('blocks', sort=True)
            text_blocks = [block for block in blocks if block[6] == 0 and len(block[4].strip()) > 3]
            if sum(len(block[4]) for block in text_blocks) > 20:
                image_path = artifact_dir / f'page-{index + 1}.png'
                # Evidence previews must work even in the profile without image embeddings.
                page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(image_path)
                # PDF layout engines often split a heading and each following line into separate blocks.
                # Group adjacent blocks within the same page so model numbers stay with their heading.
                groups = []
                pending, coordinates = [], []
                for block in text_blocks:
                    for text in split_text(block[4]):
                        if pending and len(' '.join(pending)) + len(text) > 1200:
                            groups.append((pending, coordinates))
                            pending, coordinates = [], []
                        pending.append(text)
                        coordinates.append(block[:4])
                if pending:
                    groups.append((pending, coordinates))
                for texts, boxes in groups:
                    bounds = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
                    chunks.append(ExtractedChunk('\n'.join(texts), page=index + 1, bbox=[float(v) for v in bounds], image_path=str(image_path) if image_path else None,
                                                 metadata={'coordinates': 'pdf-points', 'width': page.rect.width,
                                                           'height': page.rect.height, 'extractor': 'pymupdf'}))
            else:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image_path = artifact_dir / f'page-{index + 1}.png'
                pixmap.save(image_path)
                image_chunks = ocr_image(Image.open(io.BytesIO(pixmap.tobytes('png'))), cfg)
                if not image_chunks:
                    image_chunks = [ExtractedChunk('', 'image')]
                for chunk in image_chunks:
                    chunk.page = index + 1
                    chunk.image_path = str(image_path)
                    if chunk.bbox:
                        chunk.bbox = [v / 2 for v in chunk.bbox]
                    chunk.metadata.update({'coordinates': 'pdf-points', 'width': page.rect.width, 'height': page.rect.height})
                    chunks.append(chunk)
    return chunks


def probe_media(path: Path, cfg: Settings = settings) -> dict:
    data = json.loads(command(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))
    try:
        duration = float(data['format']['duration'])
    except (KeyError, ValueError) as exc:
        raise ValueError('Media duration cannot be determined') from exc
    if not 0 < duration <= cfg.max_duration:
        raise ValueError(f'Media exceeds the {cfg.max_duration}-second duration limit')
    if not any(s.get('codec_type') in ('audio', 'video') for s in data.get('streams', [])):
        raise ValueError('No supported audio or video stream')
    return data


_whisper_model = None


def transcribe(path: Path, cfg: Settings = settings) -> list[ExtractedChunk]:
    global _whisper_model
    weights = cfg.model_dir / 'whisper' / 'tiny.pt'
    if not weights.exists():
        raise ValueError('Local Whisper weights are missing. Run python -m worker.download_models --whisper')
    import whisper
    import torch
    torch.set_num_threads(2)
    if _whisper_model is None:
        _whisper_model = whisper.load_model(str(weights), device='cpu')
    with tempfile.TemporaryDirectory(prefix='homeatlas-audio-') as temporary:
        wav = Path(temporary) / 'audio.wav'
        command(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', '16000', str(wav)])
        result = _whisper_model.transcribe(str(wav), fp16=False, verbose=False, condition_on_previous_text=False)
    return [ExtractedChunk(segment['text'].strip(), 'transcript', start_seconds=float(segment['start']),
                           end_seconds=float(segment['end']), metadata={'model': 'openai/whisper-tiny', 'runtime': '20250625'})
            for segment in result['segments'] if segment['text'].strip()]


def extract(path: Path, mime: str, artifact_dir: Path, cfg: Settings = settings) -> list[ExtractedChunk]:
    validate_file(path, mime, cfg)
    artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if mime == 'application/pdf':
        chunks = extract_pdf(path, artifact_dir, cfg)
    elif mime.startswith('image/'):
        with Image.open(path) as picture:
            chunks = ocr_image(picture, cfg) or [ExtractedChunk('', 'image')]
        for chunk in chunks:
            chunk.image_path = str(path)
    elif mime.startswith(('audio/', 'video/')):
        media = probe_media(path, cfg)
        chunks = transcribe(path, cfg) if any(s['codec_type'] == 'audio' for s in media['streams']) else []
        if mime.startswith('video/'):
            duration = float(media['format']['duration'])
            interval = max(10, duration / 30)
            # A bounded 30 frames, each with exact sampled timestamp; never index every frame.
            for n in range(min(30, int(duration / interval) + 1)):
                timestamp = n * interval
                frame = artifact_dir / f'frame-{n:03d}.jpg'
                command(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(timestamp), '-i', str(path), '-frames:v', '1', '-vf', 'scale=1280:-2', str(frame)])
                if not frame.exists():
                    continue
                frame_chunks = ocr_image(Image.open(frame), cfg) or [ExtractedChunk('', 'image')]
                for chunk in frame_chunks:
                    chunk.image_path = str(frame)
                    chunk.start_seconds = timestamp
                    chunk.end_seconds = min(timestamp + interval, duration)
                    chunk.metadata['sample_interval_seconds'] = interval
                chunks.extend(frame_chunks)
    else:
        chunks = [ExtractedChunk(text) for text in split_text(path.read_text(encoding='utf-8'))]
    if not chunks:
        raise ValueError('No readable evidence found in this file')
    if len(chunks) > 6000:
        raise ValueError('File produces too many regions; split it into smaller sources')
    return chunks
