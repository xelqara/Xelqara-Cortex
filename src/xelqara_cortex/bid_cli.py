from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bidcore import BidCore
from .core import Cortex
from .local_model import LocalCommandAdapter, OllamaAdapter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bidcore", description="Xelqara BidCore evidence-grounded RFP drafting")
    parser.add_argument("--root", default=".cortex")
    parser.add_argument("--questions", required=True, help="JSON list of question strings")
    parser.add_argument("--output", default="bidcore_drafts.json")
    parser.add_argument("--coverage-report", help="optional JSON path for conservative pre-flight coverage analysis")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--ollama-model", help="optional local Ollama model name; loopback only")
    parser.add_argument("--local-command", help="optional local executable that reads the prompt from stdin")
    args = parser.parse_args(argv)
    cortex = Cortex(args.root)
    try:
        rows = json.loads(Path(args.questions).read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("questions file must contain a JSON list")
        model = None
        if args.ollama_model and args.local_command:
            raise ValueError("choose only one local model adapter")
        if args.ollama_model:
            model = OllamaAdapter(args.ollama_model)
        elif args.local_command:
            model = LocalCommandAdapter(args.local_command)
        bid = BidCore(cortex, model=model)
        questions = bid.parse_questions(rows)
        if args.coverage_report:
            coverage = bid.coverage_report(questions, args.limit)
            coverage_path = Path(args.coverage_report)
            coverage_path.parent.mkdir(parents=True, exist_ok=True)
            coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
        drafts = bid.draft_batch(questions, args.limit)
        bid.export_json(drafts, args.output)
        result = {"status": "ok", "questions": len(drafts), "output": str(Path(args.output).resolve())}
        if args.coverage_report:
            result["coverage_report"] = str(Path(args.coverage_report).resolve())
        print(json.dumps(result, ensure_ascii=False))
        return 0
    finally:
        cortex.close()


if __name__ == "__main__":
    raise SystemExit(main())
