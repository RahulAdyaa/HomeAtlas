# Small local RAG evaluation

13 October 2026. `node scripts/rag-evaluate.mjs` uses the actual authenticated Node handlers, real PostgreSQL, Python retrieval worker, original fictional PDF/scan fixtures, and locally run Qwen3-VL4B Instruct, BGE, SigLIP2. It does not mock a model response. The expected corpus is the two PDF records associated with the sample bedroom purifier; queries are explicitly scoped to that item. Audio/video contractor notes elsewhere in the same household are tested separately.

| Case | Expected evidence |
| --- | --- |
| Filter | AirOne manual page2, A200-HEPA |
| Warranty | Original receipt page1, 12 February2028 |
| Reset | AirOne manual page2, hold filter button5 seconds |
| Missing bill | Abstain, zero citations |
| Photo question | AirOne manual page2, A200-HEPA, with original scanned-page query image |

Results in `rag-results.json`: source recall for supported cases **4/4**, canonical citation correctness **5/5**, constrained groundedness **5/5**, missing-evidence abstention **1/1**. Inference mode for all supported cases is `local-model-grounded`; missing evidence is `abstention`. Measured end-to-end latency was filter10,639ms, warranty4,073ms, reset3,299ms, missing1,690ms, photo9,813ms. These include local retrieval/inference and HTTP processing; they are one run, not p95 measurements or production throughput guarantees.

Citation checks reopen each citation through its authorization boundary and assert the quoted text is an exact substring of its stored source and the version/page match. Whitespace-flattened model quotes are mapped back to the exact original span before Node performs its independent substring check. No punctuation/facts are silently rewritten to make a quote pass.

`PYTHONPATH=. worker/.venv/bin/python scripts/inference-safety.py` also exercised the real local model on two original synthetic records: an instruction embedded in evidence did not replace the answer, and conflicting expiry records returned `confidence=conflicting` with citations. Results are in `inference-safety-results.json`. Worker tests separately reject fabricated quotes and cross-embedding-space comparison; the Node security suite rejects foreign citations, empty/fabricated quotes and credit replay.

## Limits

Five easy, English, clearly printed cases are too small to estimate broad recall, groundedness or hallucination rates. Groundedness here measures expected source text/quotes, not factual truth of uploaded records, prose usefulness, visual damaged-part matching, multilingual quality, or legal/repair accuracy. The photo case is a readable manual-page scan; it does not establish part compatibility from an arbitrary damaged appliance photograph. Two adversarial/conflict examples do not prove resistance to arbitrary prompt injection. No independent human rating, p95 load test, full GPU BGE-M3/reranker-v2-m3/PaddleOCR evaluation, or production deployment benchmark was performed.

The initial generic Ollama4b tag was a thinking model and sometimes exhausted JSON output tokens; its extractive fallback results were excluded from the final Instruct-mode claims. Final artifact/runtime pins are in MODELS.md. Raw case metrics are preserved rather than substituting the security suite's synthetic HTTP worker for model evidence.
