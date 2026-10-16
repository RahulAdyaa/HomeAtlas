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
import csv
import posixpath
import zipfile
import xml.etree.ElementTree as ET
import re
import unicodedata
from collections import Counter

import fitz
from PIL import Image, ImageOps

from .config import Settings, settings
from .pictures import oriented_rgb


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
    elif mime in ('text/plain', 'text/markdown', 'text/csv'):
        try:
            with path.open('r', encoding='utf-8-sig') as source:
                for block in iter(lambda: source.read(1024 * 1024), ''):
                    if '\x00' in block:
                        raise ValueError('Invalid text file')
        except UnicodeDecodeError as exc:
            raise ValueError('Text and CSV files must use UTF-8 encoding') from exc
    elif mime in ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'application/vnd.ms-excel.sheet.macroenabled.12'):
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                if (len(infos) > 2000 or sum(entry.file_size for entry in infos) > 120 * 1024 * 1024
                        or any(entry.file_size > 40 * 1024 * 1024 or
                               (entry.compress_size and entry.file_size / entry.compress_size > 200)
                               for entry in infos)
                        or 'xl/workbook.xml' not in archive.namelist()):
                    raise ValueError('Spreadsheet archive exceeds safe processing limits or is invalid')
        except (zipfile.BadZipFile, OSError) as exc:
            raise ValueError('Invalid Excel workbook') from exc
    else:
        raise ValueError('Unsupported file type')


def ocr_image(picture: Image.Image, cfg: Settings = settings) -> list[ExtractedChunk]:
    picture = oriented_rgb(picture)
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
    from .ocr import read
    return [ExtractedChunk(row['text'],'ocr',bbox=row['bbox'],metadata=row['metadata'])
            for row in read(picture,cfg.ocr_languages)]


def image_context(chunks: list[ExtractedChunk], width: float, height: float) -> list[ExtractedChunk]:
    """Keep adjacent labels/values together, while retaining line-level source boxes."""
    if not chunks:
        return [ExtractedChunk('Visual source image. Inspect the attached original for evidence.', 'image',
                bbox=[0,0,width,height],metadata={'visual_anchor':True,'width':width,'height':height})]
    if len(chunks)==1:return chunks
    contexts=[]
    for offset in range(0,len(chunks),12):
        group=chunks[offset:offset+12]
        meta=dict(group[0].metadata,ocr_context=True,
                  confidence=min(c.metadata.get('confidence',100) for c in group))
        contexts.append(ExtractedChunk('\n'.join(c.text for c in group),'ocr',
            bbox=[min(c.bbox[0] for c in group),min(c.bbox[1] for c in group),
                  max(c.bbox[2] for c in group),max(c.bbox[3] for c in group)],metadata=meta))
    return contexts+chunks


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


def clean_pdf_text(raw: str, repeated_margins: set[str] | None = None) -> str:
    """Normalize searchable prose without changing page/bounding-box provenance."""
    raw = unicodedata.normalize('NFKC', raw.replace('\ufb01', 'fi').replace('\ufb02', 'fl'))
    lines = [line.strip() for line in raw.replace('\r\n', '\n').split('\n')]
    lines = [line for line in lines if line and line not in (repeated_margins or set()) and
             not re.fullmatch(r'page\s+\d{1,4}', line, re.I)]
    text = '\n'.join(lines)
    text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    return re.sub(r'[ \t]+', ' ', text).strip()


def repeated_pdf_margins(document: fitz.Document) -> set[str]:
    if len(document) < 3:
        return set()
    found = Counter()
    for page in document:
        top, bottom = page.rect.height * .1, page.rect.height * .9
        lines = set()
        for block in page.get_text('blocks'):
            if block[6] == 0 and (block[1] <= top or block[3] >= bottom):
                lines.update(line.strip() for line in block[4].splitlines() if line.strip())
        found.update(lines)
    return {line for line, count in found.items() if count >= max(2, len(document) // 2) and len(line) < 180}


def _xml_local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        source = archive.open('xl/sharedStrings.xml')
    except KeyError:
        return []
    values = []
    with source:
        for _, element in ET.iterparse(source, events=('end',)):
            if _xml_local_name(element.tag) == 'si':
                values.append(''.join(child.text or '' for child in element.iter() if _xml_local_name(child.tag) == 't'))
                element.clear()
                if len(values) > 1_000_000:
                    raise ValueError('Spreadsheet has too many shared strings')
    return values


def _xlsx_sheet_rows(archive: zipfile.ZipFile, target: str, shared: list[str], budget: list[int]):
    path = posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl', target))
    if path.startswith('../') or not path.startswith('xl/worksheets/') or path not in archive.namelist():
        raise ValueError('Invalid Excel worksheet reference')
    row_count = 0
    with archive.open(path) as source:
        for _, element in ET.iterparse(source, events=('end',)):
            if _xml_local_name(element.tag) != 'row':
                continue
            row_count += 1
            values = {}
            for cell in element:
                if _xml_local_name(cell.tag) != 'c':
                    continue
                budget[1] += 1
                if budget[1] > 500_000:
                    raise ValueError('Spreadsheet contains too many cells')
                reference = cell.attrib.get('r', '')
                column = ''.join(char for char in reference if char.isalpha()).upper()
                kind = cell.attrib.get('t', '')
                value = next((child.text for child in cell if _xml_local_name(child.tag) == 'v'), None)
                if kind == 'inlineStr':
                    value = ''.join(child.text or '' for child in cell.iter() if _xml_local_name(child.tag) == 't')
                elif kind == 's' and value is not None:
                    try:
                        value = shared[int(value)]
                    except (ValueError, IndexError) as exc:
                        raise ValueError('Excel workbook has an invalid shared string') from exc
                elif kind == 'b' and value is not None:
                    value = 'TRUE' if value == '1' else 'FALSE'
                if value is not None and str(value).strip():
                    values[column or str(len(values) + 1)] = str(value).strip()
            number = int(element.attrib.get('r', row_count))
            element.clear()
            yield number, values
            budget[0] += 1
            if budget[0] > 50_000:
                raise ValueError('Spreadsheet exceeds the 50,000 row limit')


def extract_spreadsheet(path: Path) -> list[ExtractedChunk]:
    chunks = []
    with zipfile.ZipFile(path) as archive:
        shared = _xlsx_shared_strings(archive)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
              'rel': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
              'pkg': 'http://schemas.openxmlformats.org/package/2006/relationships'}
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {item.attrib['Id']: item.attrib['Target'] for item in relationships.findall('pkg:Relationship', ns)}
        sheets = workbook.findall('main:sheets/main:sheet', ns)
        if len(sheets) > 100:
            raise ValueError('Spreadsheet exceeds the 100 worksheet limit')
        budget = [0, 0]
        for sheet in sheets:
            name = sheet.attrib.get('name', 'Sheet')[:120]
            relation_id = sheet.attrib.get(f'{{{ns["rel"]}}}id')
            if relation_id not in targets:
                raise ValueError('Excel workbook has an invalid worksheet link')
            header = {}
            pending: list[str] = []
            first_row = last_row = 0
            for row_number, cells in _xlsx_sheet_rows(archive, targets[relation_id], shared, budget):
                if not cells:
                    continue
                if not header:
                    header = {column: value for column, value in cells.items()}
                    # A header row has no answer values by itself, but remains in the text for grounding.
                    rendered = 'Headers: ' + '; '.join(f'{column}={value}' for column, value in cells.items())
                else:
                    rendered_cells = [f'{header.get(column, column)}: {value}' for column, value in cells.items()]
                    rendered = f'Row {row_number}: ' + '; '.join(rendered_cells)
                if len(rendered) > 1200:
                    for piece in split_text(rendered):
                        chunks.append(ExtractedChunk(f'Sheet {name}, row {row_number}: {piece}', metadata={
                            'sheet': name, 'row_start': row_number, 'row_end': row_number, 'extractor': 'xlsx'}))
                    continue
                if pending and sum(map(len, pending)) + len(rendered) > 1000:
                    chunks.append(ExtractedChunk(f'Sheet {name}, rows {first_row}-{last_row}:\n' + '\n'.join(pending), metadata={
                        'sheet': name, 'row_start': first_row, 'row_end': last_row, 'extractor': 'xlsx'}))
                    pending = []
                if not pending:
                    first_row = row_number
                pending.append(rendered)
                last_row = row_number
            if pending:
                chunks.append(ExtractedChunk(f'Sheet {name}, rows {first_row}-{last_row}:\n' + '\n'.join(pending), metadata={
                    'sheet': name, 'row_start': first_row, 'row_end': last_row, 'extractor': 'xlsx'}))
    return chunks


def extract_csv(path: Path) -> list[ExtractedChunk]:
    chunks = []
    pending: list[str] = []
    first_row = last_row = 0
    headers: list[str] = []
    csv.field_size_limit(1_000_000)
    with path.open('r', encoding='utf-8-sig', newline='') as source:
        reader = csv.reader(source)
        for number, row in enumerate(reader, 1):
            if number > 50_000:
                raise ValueError('CSV exceeds the 50,000 row limit')
            if len(row) > 10_000:
                raise ValueError('CSV row has too many columns')
            values = [value.strip() for value in row]
            if not any(values):
                continue
            if not headers:
                headers = values
                rendered = 'Headers: ' + '; '.join(f'{index + 1}={value}' for index, value in enumerate(values) if value)
            else:
                rendered = f'Row {number}: ' + '; '.join(
                    f'{headers[index] if index < len(headers) and headers[index] else index + 1}={value}'
                    for index, value in enumerate(values) if value)
            if len(rendered) > 1200:
                for piece in split_text(rendered):
                    chunks.append(ExtractedChunk(f'CSV row {number}: {piece}', metadata={
                        'sheet': 'CSV', 'row_start': number, 'row_end': number, 'extractor': 'csv'}))
                continue
            if pending and sum(map(len, pending)) + len(rendered) > 1000:
                chunks.append(ExtractedChunk(f'CSV rows {first_row}-{last_row}:\n' + '\n'.join(pending), metadata={
                    'sheet': 'CSV', 'row_start': first_row, 'row_end': last_row, 'extractor': 'csv'}))
                pending = []
            if not pending:
                first_row = number
            pending.append(rendered)
            last_row = number
        if pending:
            chunks.append(ExtractedChunk(f'CSV rows {first_row}-{last_row}:\n' + '\n'.join(pending), metadata={
                'sheet': 'CSV', 'row_start': first_row, 'row_end': last_row, 'extractor': 'csv'}))
    return chunks


def extract_pdf(path: Path, artifact_dir: Path, cfg: Settings = settings) -> list[ExtractedChunk]:
    chunks = []
    with fitz.open(path) as document:
        if document.is_encrypted:
            raise ValueError('Password-protected PDFs cannot be indexed')
        if len(document) > cfg.max_pdf_pages:
            raise ValueError('PDF exceeds the page limit')
        repeated_margins = repeated_pdf_margins(document)
        for index, page in enumerate(document):
            blocks = page.get_text('blocks', sort=True)
            text_blocks = [block for block in blocks if block[6] == 0 and len(block[4].strip()) > 3]
            if sum(len(block[4]) for block in text_blocks) > 20:
                image_path = artifact_dir / f'page-{index + 1}.png'
                # Evidence previews must work even in the profile without image embeddings.
                page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(image_path)
                # PDF layout engines often split a heading and each following line into separate blocks.
                # Group adjacent blocks within the same page so model numbers stay with their heading.
                groups = []
                pending, raw_pending, coordinates = [], [], []
                for block in text_blocks:
                    for text in split_text(clean_pdf_text(block[4], repeated_margins)):
                        if pending and len(' '.join(pending)) + len(text) > 1200:
                            groups.append((pending, raw_pending, coordinates))
                            pending, raw_pending, coordinates = [], [], []
                        pending.append(text)
                        raw_pending.append(block[4])
                        coordinates.append(block[:4])
                if pending:
                    groups.append((pending, raw_pending, coordinates))
                for texts, raw_texts, boxes in groups:
                    bounds = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
                    chunks.append(ExtractedChunk('\n'.join(texts), page=index + 1, bbox=[float(v) for v in bounds], image_path=str(image_path) if image_path else None,
                                                 metadata={'coordinates': 'pdf-points', 'width': page.rect.width,
                                                           'height': page.rect.height, 'extractor': 'pymupdf',
                                                           'raw_text': '\n'.join(raw_texts)[:16000],
                                                           'requires_visual_evidence': bool(page.get_images() or page.get_drawings())}))
                for info in sorted(page.get_image_info(),key=lambda i:fitz.Rect(i['bbox']).get_area(),reverse=True)[:8]:
                    rect=fitz.Rect(info['bbox']) & page.rect
                    if rect.is_empty or rect.width*rect.height<2500:continue
                    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=rect,alpha=False)
                    with Image.open(io.BytesIO(pix.tobytes('png'))) as embedded:
                        extra=image_context(ocr_image(embedded,cfg),pix.width,pix.height)
                    for chunk in extra:
                        # Deduplicate native text, preserve raster-only labels and numeric values.
                        if chunk.text.strip() in ' '.join(b[4] for b in text_blocks):continue
                        chunk.page=index+1
                        chunk.image_path=str(image_path)
                        chunk.bbox=[chunk.bbox[0]/2+rect.x0,chunk.bbox[1]/2+rect.y0,
                                    chunk.bbox[2]/2+rect.x0,chunk.bbox[3]/2+rect.y0]
                        chunk.metadata.update(coordinates='pdf-points',width=page.rect.width,height=page.rect.height,extractor='mixed-pdf-ocr')
                        chunks.append(chunk)
            else:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image_path = artifact_dir / f'page-{index + 1}.png'
                pixmap.save(image_path)
                image_chunks = image_context(ocr_image(Image.open(io.BytesIO(pixmap.tobytes('png'))),cfg),pixmap.width,pixmap.height)
                if not image_chunks:
                    image_chunks = image_context([],pixmap.width,pixmap.height)
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
            oriented=ImageOps.exif_transpose(picture)
            chunks = image_context(ocr_image(picture,cfg),oriented.width,oriented.height)
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
    elif mime in ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'application/vnd.ms-excel.sheet.macroenabled.12'):
        chunks = extract_spreadsheet(path)
    elif mime == 'text/csv':
        chunks = extract_csv(path)
    else:
        chunks = [ExtractedChunk(text, metadata={'extractor': 'text'})
                  for text in split_text(path.read_text(encoding='utf-8-sig'))]
    if not chunks:
        raise ValueError('No readable evidence found in this file')
    if len(chunks) > 6000:
        raise ValueError('File produces too many regions; split it into smaller sources')
    return chunks
