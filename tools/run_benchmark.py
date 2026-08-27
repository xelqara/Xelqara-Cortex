from pathlib import Path
import json
import tempfile
from collections import Counter

from xelqara_cortex.core import Cortex
from xelqara_cortex.bidcore import BidCore

ROOT = Path(__file__).resolve().parents[1]
benchmark = json.loads((ROOT / "examples/rfp_benchmark_100.json").read_text(encoding="utf-8"))
library = json.loads((ROOT / "examples/rfp_answer_library_synthetic.json").read_text(encoding="utf-8"))

with tempfile.TemporaryDirectory() as tmp:
    cortex = Cortex(tmp)
    for item in library:
        cortex.ingest_text(item["evidence_source"] + "/" + item["id"], f"Question pattern: {item['question_pattern']}\nApproved answer: {item['approved_answer']}\nSource status: synthetic benchmark only.")
    bid = BidCore(cortex)
    results = []
    for index, item in enumerate(benchmark, 1):
        evidence = cortex.search(item["question"], limit=3)
        exact = any(item["question"].casefold() in e.text.casefold() for e in evidence)
        expected = index <= len(library)
        results.append({"trial": index, "id": item["id"], "category": item["category"], "expected_supported": expected, "retrieved": bool(evidence), "exact_source_match": exact, "top_score": evidence[0].score if evidence else 0.0, "predicted_supported": bool(evidence) and exact})
    supported = [r for r in results if r["expected_supported"]]
    gaps = [r for r in results if not r["expected_supported"]]
    report = {"trials": len(results), "synthetic_only": True, "supported_cases": len(supported), "gap_cases": len(gaps), "supported_exact_source_rate": round(sum(r["exact_source_match"] for r in supported) / len(supported), 4), "gap_false_support_rate": round(sum(r["predicted_supported"] for r in gaps) / len(gaps), 4), "retrieval_rate_all": round(sum(r["retrieved"] for r in results) / len(results), 4), "category_counts": dict(Counter(r["category"] for r in results)), "results": results, "interpretation": "Deterministic retrieval benchmark only; not a generative model or production accuracy evaluation."}
    output = ROOT / "reports/rfp_100_eval.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False, indent=2))
