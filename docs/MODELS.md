# Self-hosted model and runtime record

Reviewed 13 October 2026. No model inference calls a paid or hosted provider. Artifact downloads are explicit setup operations; household records are not sent during model download. The worker resolves pinned local HF snapshots and uses `local_files_only=True`, disables remote code, and calls the administrator-configured Ollama server.

## Verified lower-resource profile

| Function | Model/artifact | License | Pin |
| --- | --- | --- | --- |
| Generation and vision | Qwen3-VL 4B Instruct, Ollama `qwen3-vl:4b-instruct`, quantization Q4_K_M, about 3.3 GB | Apache-2.0 | Ollama digest `ee4b975b58c17ce268cd19d40db35d5edc64603035d2ffc1fee1968eb0947f7b` |
| Text embeddings | `BAAI/bge-small-en-v1.5`, 384 dimensions | MIT | HF `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` |
| Text reranking | `BAAI/bge-reranker-base` | MIT | HF `2cfc18c9415c912f9d8155881c133215df768a70` |
| Image/text space | `google/siglip2-base-patch16-224`, 768 dimensions | Apache-2.0 | HF `75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2` |
| Transcription | OpenAI Whisper `tiny`, local `tiny.pt`, package `openai-whisper==20250625` | MIT | SHA256 `65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9` |
| OCR | Tesseract 5.5.3, local English data, `pytesseract==0.3.13` | Apache-2.0 | Installed local executable; not a hosted OCR service |

Cards: [Qwen](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), [BGE small](https://huggingface.co/BAAI/bge-small-en-v1.5), [BGE reranker](https://huggingface.co/BAAI/bge-reranker-base), [SigLIP2](https://huggingface.co/google/siglip2-base-patch16-224), [Whisper](https://github.com/openai/whisper), [Tesseract](https://github.com/tesseract-ocr/tesseract).

Python 3.12.2; torch 2.7.0; transformers 4.57.3; FastAPI 0.115.12; Uvicorn 0.34.0; NumPy 1.26.4; PyMuPDF 1.25.5; Pillow 11.1.0. FFmpeg/FFprobe 4.2.2 prepared the test media. Direct versions are in `worker/requirements.txt`, the tested isolated transitive set in `worker/requirements.lock.txt`. The virtual environment does not inherit Anaconda packages. Earlier exploratory runs used PyMuPDF 1.23.8, Pillow10.4.0 and FastAPI0.104.1; final dependency isolation/reverification supersedes those exploratory results.

Ollama owns Apple Metal inference for the quantized Qwen artifact. BGE, SigLIP and Whisper currently use CPU in the Python worker with bounded thread counts. A 16 GiB Mac can exercise this profile; simultaneous model initialization can increase latency and memory pressure. Read measured results in RAG_EVALUATION.md rather than assuming GPU-scale throughput.

## Artifact installation

Start Ollama, then:

```sh
bash scripts/models.sh
```

This runs `ollama pull qwen3-vl:4b-instruct` and the pinned HF/Whisper downloader. HF snapshots live in the configured `HF_HOME` or default `~/.cache/huggingface/hub`; Whisper weights live in `data/models/whisper/tiny.pt`. Preserve the exact Ollama digest alongside releases because a tag can change. To verify a release, inspect the local `/api/tags` digest and compare it with the record above. There is no silent runtime model download.

Disable image embeddings with `IMAGE_EMBEDDING_MODEL=` for a lower-memory profile. OCR and Qwen image input remain distinct capabilities; an image question with missing visual retrieval is explicitly qualified. Disable `GENERATION_MODEL=` for extractive-only development. Missing model files produce explicit unavailable/extractive/abstention diagnostics, not a fake generated answer. Text and image model identities/dimensions are checked before comparing vectors.

## Full requested production profile

The original request proposed `BAAI/bge-m3`, `BAAI/bge-reranker-v2-m3`, and PaddleOCR. Their current model cards/licenses were reviewed: [BGE-M3](https://huggingface.co/BAAI/bge-m3) lists MIT, [reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) lists Apache-2.0, and [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) is Apache-2.0. Qwen and SigLIP match the requested family.

BGE-M3 and reranker-v2-m3 weights were **not installed or exercised** in this run, and no unverified HF revision is invented for them. The inspected machine instead uses the smaller cached BGE pair as a documented development decision. Switching requires pinning approved artifact revisions in environment variables, reindexing with the new model identity, and rerunning evaluation. The current generic BGE CLS path does not implement BGE-M3's sparse/multi-vector outputs.

PaddleOCR is an optional backend; its integration branch calls the PaddleOCR2 API. The supplied branch's suggested PaddleOCR2.10/PaddlePaddle3 extras were not installed or verified. Use the verified Tesseract path locally; validate the Paddle runtime on the target GPU before claiming support. A dedicated 24 GiB GPU and 32–64 GiB host RAM is the recommended starting capacity for the full profile, not a measured production performance guarantee.

## Evidence safety

Qwen receives evidence as untrusted data and produces structured explanations with exact source quotations under a JSON schema. Retrieved source-page images can support diagrams and chart values; a second local model pass reviews explanation sections. See DETAILED_ANSWERS.md for the grounding boundaries and visual provenance. Python and Node both verify the source/version and quoted substring before returning citations. This rejects fabricated quotation spans and foreign source references. Synthesized explanations and visual interpretations rely on model review; they can still contain mistakes. These checks do not establish that every uploaded statement is true or that a visually similar part is compatible. Missing or conflicting evidence is surfaced. Any electrical/gas/structural query includes a professional-work qualification. Use a larger adversarial evaluation set before public deployment.

The exploratory generic `qwen3-vl:4b` tag selected the thinking variant. It sometimes exhausted its output budget and triggered labeled extractive fallback. The final tested configuration uses explicit `4b-instruct`, its API-reported digest above, a constrained JSON schema, and verbatim source-span verification. The raw on-disk manifest file hash differs from the API artifact digest because of local manifest serialization; release identity is the API digest.
