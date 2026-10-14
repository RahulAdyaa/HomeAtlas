"""Real local vision and detailed-answer check using original CC0 fixtures."""
import json
import sys
from pathlib import Path
import uuid
from worker.ingestion import extract
from worker.models import models
from worker.config import settings
from worker.retrieval import answer_from_evidence
root = settings.storage / "answer-check"
root.mkdir(parents=True, exist_ok=True)
results = []
for modality, question in [
    ("text", "Explain and compare the warranty durations, service inspection intervals and provider for units T1, T2, T3 and T4."),
    ("table", "Explain table 1 completely. Show Eco, Normal and Boost power in watts and monthly cost in USD in a Markdown table."),
    ("chart", "Explain chart 1: what are the January, February and March values, units, and overall trend?")]:
    if len(sys.argv)>1 and modality != sys.argv[1]: continue
    chunks = extract(Path("evaluation/fixtures") / (modality + ".pdf"), "application/pdf", root / modality)
    evidence = [dict(id=uuid.uuid4(), source_id=uuid.uuid4(), version_id=uuid.uuid4(), title=modality + ".pdf",
        text=c.text, page=c.page, bbox=c.bbox, image_path=c.image_path, metadata=c.metadata, lexical_score=1)
        for c in (chunks[:1] if modality in ("chart", "table") else chunks[:4])]
    generate = models.generate
    raw = generate(question, evidence)
    (root / (modality + "-raw.json")).write_text(json.dumps(raw, indent=2))
    models.generate = lambda *args, **kwargs: raw
    reply = answer_from_evidence(question, evidence, models)
    models.generate = generate
    (root / (modality + "-result.json")).write_text(json.dumps(reply, indent=2))
    assert reply["citations"], reply
    assert reply["mode"] == "local-model-explained", reply
    assert len(reply["answer"]) > 300, reply
    if modality == "chart":
        assert "65" in reply["answer"] and "kWh" in reply["answer"], reply
    if modality == "table":
        assert "71" in reply["answer"] and "USD" in reply["answer"] and "|" in reply["answer"], reply
    results.append({"modality": modality, "mode": reply["mode"], "characters": len(reply["answer"]), "citations": len(reply["citations"])})
print(json.dumps(results))
