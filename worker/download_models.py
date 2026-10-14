"""Explicit setup command; downloads model artifacts, never uploads household content."""
import argparse
from .config import settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--whisper', action='store_true')
    parser.add_argument('--text', action='store_true')
    parser.add_argument('--image', action='store_true')
    args = parser.parse_args()
    if args.whisper:
        import whisper
        whisper.load_model('tiny', device='cpu', download_root=str(settings.model_dir / 'whisper'))
        print('Downloaded local Whisper tiny with built-in SHA256 verification')
    if args.text or args.image:
        from huggingface_hub import snapshot_download
        pairs = [(settings.text_model, settings.text_revision), (settings.reranker_model, settings.reranker_revision)] if args.text else []
        if args.image:
            if not settings.image_model or not settings.image_revision:
                raise SystemExit('Configure IMAGE_EMBEDDING_MODEL and its pinned IMAGE_EMBEDDING_REVISION first')
            pairs.append((settings.image_model, settings.image_revision))
        for name, revision in pairs:
            snapshot_download(name, revision=revision)
            print(f'Downloaded {name}@{revision}')


if __name__ == '__main__':
    main()
