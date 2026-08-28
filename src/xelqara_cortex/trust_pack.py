"""Portable, local Trust Pack export for reviewed BidCore projects."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .core import Cortex
from .enterprise import EnterpriseStore


def build_trust_pack(cortex: Cortex, store: EnterpriseStore, project_id: str, output: str | Path) -> dict[str, object]:
    row = store.db.execute("SELECT id, name, customer_label, status, created_at FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        raise ValueError("unknown project")
    approved = store.list_reviews(project_id, state="approved")
    all_reviews = store.list_reviews(project_id)
    payload = {
        "format": "xelqara-trust-pack/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "project": {"project_id": row[0], "name": row[1], "customer_label": row[2], "status": row[3], "created_at": row[4]},
        "coverage": {"total_review_items": len(all_reviews), "approved_items": len(approved), "pending_or_other_items": len(all_reviews) - len(approved)},
        "approved_answers": [asdict(item) for item in approved],
        "source_inventory": cortex.source_inventory(),
        "audit": store.audit_log(project_id),
        "policy": "This pack contains only locally reviewed answers and provenance. Human approval remains required before customer submission.",
    }
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(destination), "format": payload["format"], "approved_items": len(approved), "total_review_items": len(all_reviews), "sources": len(payload["source_inventory"]), "policy": payload["policy"]}
