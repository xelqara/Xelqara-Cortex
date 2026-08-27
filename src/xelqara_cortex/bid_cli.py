from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bidcore import BidCore
from .core import Cortex


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bidcore", description="Xelqara BidCore evidence-grounded RFP drafting")
    parser.add_argument("--root", default=".cortex")
    parser.add_argument("--questions", required=True, help="JSON list of question strings")
    parser.add_argument("--output", default="bidcore_drafts.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    cortex = Cortex(args.root)
    try:
        rows = json.loads(Path(args.questions).read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("questions file must contain a JSON list")
        bid = BidCore(cortex)
        questions = bid.parse_questions(rows)
        drafts = bid.draft_batch(questions, args.limit)
        bid.export_json(drafts, args.output)
        print(json.dumps({"status": "ok", "questions": len(drafts), "output": str(Path(args.output).resolve())}, ensure_ascii=False))
        return 0
    finally:
        cortex.close()


if __name__ == "__main__":
    raise SystemExit(main())
