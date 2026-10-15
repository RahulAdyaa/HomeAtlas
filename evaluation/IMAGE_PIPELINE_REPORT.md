# Image evidence regression results

Four fictional fixtures; this is not a customer-data accuracy estimate. Exact identifier matching uses the authored string, without numeric correction.

| Case | Previous exact field | Updated exact field | Label + value together | Old OCR ms | Updated extraction ms |
|---|---|---|---|---:|---:|
| card.png | True | True | True | 132 | 254 |
| rotated-card.png | False | True | True | 138 | 978 |
| small-card.png | True | True | True | 68 | 185 |
| mixed.pdf | False | True | True | 4 | 269 |

Previous means original PSM-6 OCR for images and native-text extraction for the mixed PDF. Updated time includes language selection, bounded layout/orientation passes and context grouping. Better recovery costs extra processing time.

Automated tests also cover source coordinates, visual-only text retrieval, citable image anchors, and retaining immutable originals. Real upload-to-answer results are recorded separately by `scripts/image-upload-qa.mjs`.

Limits: tiny text, blur, handwriting, perspective distortion and complex charts can still fail. Visual similarity only selects candidates. Generated visual claims require a separate image review; low-confidence identifier answers abstain. Existing uploads need reprocessing to obtain the improved OCR index.

Live HTTP checks passed for the rotated PNG and mixed-content PDF: authentication, multipart upload, durable ingestion, asking the serial-number question, exact authored identifier recovery, and canonical citations all passed in `local-model-explained` mode. See `image-live-results.json`. This uses only fictional data.

The affected household's five eligible existing PDF/image sources were reindexed. Aggregate checks showed all sources ready, five upgraded indexes, and zero additional credit charges. No identifiers or document contents were printed during this check.

The real local diagram and chart answers contained the expected terms HEPA and 65 kWh, respectively, with canonical source quotations (`visual-grounding-results.json`). These are term-presence checks, not an independent semantic-quality score or a general visual-accuracy estimate.

A separate transparent-background image regression also passes, alongside uncertain-identifier and visual-anchor abstention tests.
