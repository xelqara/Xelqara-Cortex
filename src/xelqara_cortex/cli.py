from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import Cortex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cortex", description="Xelqara Cortex local-first cognitive context engine")
    parser.add_argument("--root", default=".cortex", help="local Cortex data directory")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="ingest a UTF-8 text/Markdown file")
    ingest.add_argument("path")
    ingest.add_argument("--name", help="logical source name")
    ingest.add_argument("--replace", action="store_true")
    ask = sub.add_parser("ask", help="retrieve evidence and produce an offline answer")
    ask.add_argument("question")
    ask.add_argument("--limit", type=int, default=5)
    search = sub.add_parser("search", help="search local evidence")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    remember = sub.add_parser("remember", help="store a durable local memory")
    remember.add_argument("content")
    remember.add_argument("--kind", default="general")
    memories = sub.add_parser("memories", help="list durable local memories")
    memories.add_argument("--kind")
    memories.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cortex = Cortex(args.root)
    try:
        if args.command == "ingest":
            count = cortex.ingest_file(args.path, args.name, args.replace)
            print(json.dumps({"status": "ok", "chunks": count, "root": str(Path(args.root).resolve())}, ensure_ascii=False))
        elif args.command == "search":
            print(json.dumps([item.__dict__ for item in cortex.search(args.query, args.limit)], ensure_ascii=False, indent=2))
        elif args.command == "ask":
            print(json.dumps(cortex.export_answer(cortex.answer_offline(args.question, args.limit)), ensure_ascii=False, indent=2))
        elif args.command == "remember":
            memory_id = cortex.remember(args.content, args.kind)
            print(json.dumps({"status": "ok", "memory_id": memory_id, "kind": args.kind}, ensure_ascii=False))
        elif args.command == "memories":
            print(json.dumps(cortex.list_memories(args.kind, args.limit), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        cortex.close()


if __name__ == "__main__":
    raise SystemExit(main())
