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
        drafts = bid.draft_batch(questions, args.limit)
        bid.export_json(drafts, args.output)
        print(json.dumps({"status": "ok", "questions": len(drafts), "output": str(Path(args.output).resolve())}, ensure_ascii=False))
        return 0
    finally:
        cortex.close()


if __name__ == "__main__":
    raise SystemExit(main())
