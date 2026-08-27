from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .bidcore import BidCore
from .core import Cortex
from .document_io import DocumentImporter
from .enterprise import EnterpriseStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bidcore-enterprise", description="Xelqara BidCore enterprise workflow")
    parser.add_argument("--root", default=".cortex")
    sub = parser.add_subparsers(dest="command", required=True)
    ws = sub.add_parser("workspace")
    ws.add_argument("name")
    ws.add_argument("--owner", required=True)
    project = sub.add_parser("project")
    project.add_argument("workspace_id")
    project.add_argument("name")
    project.add_argument("--customer", default="Private customer")
    project.add_argument("--by", required=True)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("project_id")
    ingest.add_argument("document")
    ingest.add_argument("--name")
    ingest.add_argument("--by", required=True)
    draft = sub.add_parser("draft")
    draft.add_argument("project_id")
    draft.add_argument("questions")
    draft.add_argument("--by", required=True)
    draft.add_argument("--limit", type=int, default=3)
    review = sub.add_parser("review")
    review.add_argument("item_id")
    review.add_argument("state", choices=["in_review", "approved", "changes_requested", "rejected", "pending_review"])
    review.add_argument("--by", required=True)
    review.add_argument("--note")
    export = sub.add_parser("export")
    export.add_argument("project_id")
    export.add_argument("output")
    audit = sub.add_parser("audit")
    audit.add_argument("--target")
    args = parser.parse_args(argv)
    cortex = Cortex(args.root)
    store = EnterpriseStore(args.root)
    try:
        if args.command == "workspace":
            print(json.dumps(asdict(store.create_workspace(args.name, args.owner)), ensure_ascii=False, indent=2))
        elif args.command == "project":
            print(json.dumps(asdict(store.create_project(args.workspace_id, args.name, args.customer, args.by)), ensure_ascii=False, indent=2))
        elif args.command == "ingest":
            count = cortex.ingest_file(args.document, args.name, replace=True)
            print(json.dumps({"status": "ok", "chunks": count}, ensure_ascii=False))
        elif args.command == "draft":
            question_path = Path(args.questions)
            if question_path.suffix.lower() == ".json":
                rows = json.loads(question_path.read_text(encoding="utf-8"))
                questions = BidCore.parse_questions(rows)
            else:
                chunks = DocumentImporter().import_file(question_path)
                questions = BidCore.parse_document_chunks(chunks)
            drafts = BidCore(cortex).draft_batch(questions, args.limit)
            count = store.add_reviews(args.project_id, drafts, args.by)
            print(json.dumps({"status": "ok", "review_items": count}, ensure_ascii=False))
        elif args.command == "review":
            store.transition(args.item_id, args.state, args.by, args.note)
            print(json.dumps({"status": "ok", "item_id": args.item_id, "state": args.state}, ensure_ascii=False))
        elif args.command == "export":
            if Path(args.output).suffix.lower() == ".json":
                store.export_json(args.project_id, args.output)
            else:
                store.export_csv(args.project_id, args.output)
            print(json.dumps({"status": "ok", "output": str(Path(args.output).resolve())}, ensure_ascii=False))
        elif args.command == "audit":
            print(json.dumps(store.audit_log(args.target), ensure_ascii=False, indent=2))
        return 0
    finally:
        store.close()
        cortex.close()


if __name__ == "__main__":
    raise SystemExit(main())
