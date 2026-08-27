"""Governed evidence registry for BidCore."""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path

@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source: str
    owner: str
    classification: str
    approval: str
    reviewed_at: str | None
    review_due_at: str | None
    checksum: str

class EvidenceRegistry:
    def __init__(self, root: str | Path = ".cortex") -> None:
        root = Path(root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(root / "enterprise.db")
        self.db.execute("CREATE TABLE IF NOT EXISTS evidence_registry (id TEXT PRIMARY KEY, source TEXT NOT NULL, owner TEXT NOT NULL, classification TEXT NOT NULL, approval TEXT NOT NULL, reviewed_at TEXT, review_due_at TEXT, checksum TEXT NOT NULL)")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _checksum(source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()

    def register(self, source: str, owner: str, classification: str = "internal", approval: str = "pending", reviewed_at: str | None = None, review_due_at: str | None = None) -> EvidenceRecord:
        if classification not in {"public", "internal", "confidential", "restricted"}:
            raise ValueError("invalid classification")
        if approval not in {"pending", "approved", "rejected", "expired"}:
            raise ValueError("invalid approval")
        evidence_id = self._checksum(source)[:24]
        record = EvidenceRecord(evidence_id, source, owner, classification, approval, reviewed_at, review_due_at, self._checksum(source))
        self.db.execute("INSERT OR REPLACE INTO evidence_registry(id,source,owner,classification,approval,reviewed_at,review_due_at,checksum) VALUES(?,?,?,?,?,?,?,?)", (record.evidence_id, record.source, record.owner, record.classification, record.approval, record.reviewed_at, record.review_due_at, record.checksum))
        self.db.commit()
        return record

    def get(self, source: str) -> EvidenceRecord | None:
        row = self.db.execute("SELECT id,source,owner,classification,approval,reviewed_at,review_due_at,checksum FROM evidence_registry WHERE source=?", (source,)).fetchone()
        return EvidenceRecord(*row) if row else None

    def stale(self, now: str | None = None) -> list[EvidenceRecord]:
        now = now or datetime.now(UTC).isoformat()
        rows = self.db.execute("SELECT id,source,owner,classification,approval,reviewed_at,review_due_at,checksum FROM evidence_registry WHERE approval='expired' OR (review_due_at IS NOT NULL AND review_due_at < ?)", (now,)).fetchall()
        return [EvidenceRecord(*row) for row in rows]
