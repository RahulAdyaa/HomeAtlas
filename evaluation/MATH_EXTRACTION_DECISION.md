# PDF equation handling

HomeAtlas already uses PyMuPDF for text and page coordinates and a local Qwen3-VL model for image-grounded generation and a separate evidence review. This change retains that stack. PDF text is cleaned for retrieval, while formula-like blocks are flagged for visual review; their source page and bounding box are preserved. The answer may contain LaTeX only when the model's separate source review accepts it. When text extraction is uncertain, the citation displays a crop from the original PDF page, linked to the full page.

The equation flag is a conservative display hint, not an equation OCR confidence score. It can miss formulas with no detectable operator or include ordinary equalities. We have not benchmarked a specialized math parser against Qwen3-VL or measured formula transcription accuracy, so this is an honest visual fallback rather than a claim that equations are converted reliably.
