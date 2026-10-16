# Independent review of saved HomeAtlas answers

**Bounded review: 43/60 questions from one stopped generation run; 37 answerable, 6 authored negatives, and no scanned-PDF generation.** Three independent Codex review assignments covered disjoint text, table, and visual partitions. This is not a RAGAS score, human review, calibrated multi-rater evaluation, or production accuracy estimate. The exact Codex serving model ID was unavailable; the answer generator was the separate self-hosted `qwen3-vl:4b-instruct`.

Primary answerable correctness: **30.5/37 = 0.824324 (null=0)**. This includes 30 fully correct answers, one half-credit answer, and six zero-credit answers. The six authored negatives are separate: **6/6 = 1.000000 appropriate abstentions**. Including those negatives would give 36.5/43 = 0.848837 (null=0); that is not the answerable-only correctness score.

| Review measure | Exact accounting |
| --- | --- |
| Faithfulness | 35/36 = 0.972222 (null=7); seven non-substantive refusals excluded |
| Answer relevancy | 31.5/37 = 0.851351 (null=6); six appropriate negative abstentions excluded |
| Explicit hallucination flags, all reviewed answers | 2/43 = 0.046512 |
| Explicit hallucination flags, answerable only | 2/37 = 0.054054 |
| Explicit hallucination flags, substantive answers only | 2/36 = 0.055556 |
| False refusals on answerable questions | 1/37 = 0.027027 (`text-10`) |
| Citation claim support, categorical per answer | 27 supported / 9 partial / 0 unsupported / 7 none |
| Fully supported citation judgments, excluding none | 27/36 = 0.750000; not claim-count precision/recall |

Null faithfulness/relevancy values are excluded, not converted into zero or one. Hallucination rates count explicit unsupported factual-claim flags, not refusals. A table reviewer used `abstention_appropriate=false` for correctly answered positives, so false refusals are derived from saved `metrics.abstained` and authored answerability.

| Modality | Reviewed / answerable / negatives | Answerable correctness | Negative abstention | Faithfulness | Relevancy | Hallucination flags (all reviewed) | Citation support: supported / partial / unsupported / none |
| --- | --- | --- | --- | --- | --- | --- | --- |
| text | 12 / 10 / 2 | 9/10 = 0.900000 (null=0) | 2/2 = 1.000000 | 9/9 = 1.000000 (null=3) | 9/10 = 0.900000 (null=2) | 0/12 = 0.000000 | 9 / 0 / 0 / 3 |
| table | 12 / 10 / 2 | 10/10 = 1.000000 (null=0) | 2/2 = 1.000000 | 10/10 = 1.000000 (null=2) | 10/10 = 1.000000 (null=2) | 0/12 = 0.000000 | 10 / 0 / 0 / 2 |
| image | 12 / 10 / 2 | 6.5/10 = 0.650000 (null=0) | 2/2 = 1.000000 | 9/10 = 0.900000 (null=2) | 6.5/10 = 0.650000 (null=2) | 2/12 = 0.166667 | 5 / 5 / 0 / 2 |
| chart | 7 / 7 / 0 | 5/7 = 0.714286 (null=0) | NOT MEASURED (n=0) | 7/7 = 1.000000 (null=0) | 6/7 = 0.857143 (null=0) | 0/7 = 0.000000 | 3 / 4 / 0 / 0 |
| scanned | 0 / 0 / 0 | NOT MEASURED (n=0; null=0) | NOT MEASURED (n=0) | NOT MEASURED (n=0; null=0) | NOT MEASURED (n=0; null=0) | NOT MEASURED (n=0) | 0 / 0 / 0 / 0 |

**Observed failures must remain visible.** `text-10` falsely refused the answerable four-unit service-interval summary. `image-02`, `image-04`, and `image-10` quoted labels but omitted the requested visual relationships. `chart-01` did not bind March to its usage and `chart-02` did not state the trend. `image-06` received half credit and an unsupported-claim flag; `image-08` answered the core question correctly but also received an unsupported-claim flag. Partial citation support also includes unrelated citations in `chart-03` and `chart-07`. These are the original reviewers’ findings, not new judgments by the aggregator.

For the 17 answerable image/chart cases combined, correctness is 11.5/17 = 0.676471 (null=0). High faithfulness of quoted material does not establish that the response answered its visual question.

Still **NOT MEASURED**: exact semantic context precision@5/recall, claim-count citation precision/recall, external RAGAS LLM-judge scores, scanned generation quality, inter-rater agreement, repeat-run semantic stability, and production generalization. No confidence interval or baseline semantic-improvement claim is added for this review.

Artifacts: [aggregate JSON](results/independent-judge-summary.json), [text judgments](results/independent-judge-text.json), [table judgments](results/independent-judge-table.json), [visual judgments](results/independent-judge-visual.json). The showcase report incorporates this same aggregation.

## Provenance and regeneration

Saved generation source: `results/generation-agent.json`, `final-run-01`, SHA-256 `f7691e586c7aa84eff810dd3fe4e86ca647a2a5bdaee3a03bbaef3c2e1a66b82`.
Dataset fingerprint: `0bf5aba28055da78843f3a973c1886f79624dd3909bb48c6c032f3986c543fda`. Application source fingerprint: `b253dd629e6ab18415e3bccf0448566e123f81907f631daa1407b51b588c95c8`.

| Review input | SHA-256 | Questions |
| --- | --- | --- |
| `results/independent-judge-text.json` | `39672aefed7233d29c2c06e08feeca6df056451522b1ddce896f1a41923232fb` | 12 |
| `results/independent-judge-table.json` | `ae6a3602fa243180111de9cf463bf522da1999f6a95733f7d81cf7e969f779b4` | 12 |
| `results/independent-judge-visual.json` | `ffe6af162a32277139fa678556c478725884b1104ce9b202de900c0970524f12` | 19 |

The aggregator checks source fingerprints/digests, unique IDs, exact 43-row coverage, rubric score types, and answerability against saved generation data. It recomputes every numerator and denominator from case rows; source-artifact summaries are not trusted as aggregates. No new app inference or judge scoring runs.

```sh
python3 evaluation/showcase/independent_review.py
evaluation/.venv/bin/python evaluation/showcase/report.py --app-root "$PWD"
```

The first command regenerates the aggregate JSON and this review; the second regenerates the showcase JSON and report with the same review section and coverage rows. The frozen original evaluation runner remains historical and unchanged; do not invoke it to replace this budget-limited showcase report.

Evidence limits: text review used saved excerpts/references; table and visual reviewers inspected original fictional pages. Some original pages contain facts absent from the exact OCR excerpt. No multiple-rater agreement or human expert adjudication was performed. The non-random stopped prefix and one observed generation run cannot estimate real-household or scanned-document performance.
