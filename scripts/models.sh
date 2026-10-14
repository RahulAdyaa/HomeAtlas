#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ollama >/dev/null || { echo 'Install and start Ollama first.'; exit 1; }
ollama pull qwen3-vl:4b-instruct
worker/.venv/bin/python -m worker.download_models --text --image --whisper
printf '\nPinned text retrieval, reranker and Whisper models are installed.\n'
