"""Enterprise workflow primitives for Xelqara BidCore.

The module is intentionally local-first and dependency-light. It provides
workspace/project records, role checks, review transitions, audit events, and
portable JSON/CSV exports. It never submits a proposal or calls an external
service.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

_ROLES = {"owner", "admin", "reviewer", "contributor", "viewer"}
_TRANSITIONS = {
    "pending_review": {"in_review", "rejected"},
    "in_review": {"approved", "changes_requested", "rejected"},
    "changes_requested": {"in_review", "rejected"},
    "approved": {"in_review"},
    "rejected": {"pending_review"},
}

@dataclass(frozen=True)
class Workspace:
    workspace_id: str
    name: str
    owner: str
    created_at: str

@dataclass(frozen=True)
class Project:
    project_id: str
    workspace_id: str
    name: str
    customer_label: str
    status: str
    created_at: str

@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    project_id: str
    question_id: str
    question: str
    category: str
    draft: str
    sources: list[str]
    confidence: str
    review: str
    warning: str | None = None
    reviewer: str | None = None
    reviewer_note: str | None = None

class EnterpriseStore:
    def __init__(self, root: str | Path = ".cortex") -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "enterprise.db")
        self.db.execute("CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL, created_at TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, name TEXT NOT NULL, customer_label TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS members (workspace_id TEXT NOT NULL, actor TEXT NOT NULL, role TEXT NOT NULL, PRIMARY KEY(workspace_id, actor))")
        self.db.execute("CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, question_id TEXT NOT NULL, question TEXT NOT NULL, category TEXT NOT NULL, draft TEXT NOT NULL, sources TEXT NOT NULL, confidence TEXT NOT NULL, review TEXT NOT NULL, warning TEXT, reviewer TEXT, reviewer_note TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS audit (id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL)")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _id(*parts: str) -> str:
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _audit(self, actor: str, action: str, target: str, detail: dict) -> None:
        created = self._now()
        event_id = self._id(actor, action, target, created)
        self.db.execute("INSERT INTO audit(id, actor, action, target, detail, created_at) VALUES(?,?,?,?,?,?)", (event_id, actor, action, target, json.dumps(detail, ensure_ascii=False), created))

    def create_workspace(self, name: str, owner: str) -> Workspace:
        if not name.strip() or not owner.strip():
            raise ValueError("workspace name and owner are required")
        created = self._now()
        workspace = Workspace(self._id("workspace", name, owner), name.strip(), owner.strip(), created)
        self.db.execute("INSERT OR IGNORE INTO workspaces(id,name,owner,created_at) VALUES(?,?,?,?)", (workspace.workspace_id, workspace.name, workspace.owner, workspace.created_at))
        self.db.execute("INSERT OR REPLACE INTO members(workspace_id,actor,role) VALUES(?,?,?)", (workspace.workspace_id, owner, "owner"))
        self._audit(owner, "workspace_created", workspace.workspace_id, {"name": name})
        self.db.commit()
        return workspace

    def add_member(self, workspace_id: str, actor: str, role: str, by: str) -> None:
        if role not in _ROLES:
            raise ValueError(f"role must be one of {sorted(_ROLES)}")
        if self.role(workspace_id, by) not in {"owner", "admin"}:
            raise PermissionError("only owner or admin can add members")
        self.db.execute("INSERT OR REPLACE INTO members(workspace_id,actor,role) VALUES(?,?,?)", (workspace_id, actor.strip(), role))
        self._audit(by, "member_added", workspace_id, {"actor": actor, "role": role})
        self.db.commit()

    def role(self, workspace_id: str, actor: str) -> str | None:
        row = self.db.execute("SELECT role FROM members WHERE workspace_id=? AND actor=?", (workspace_id, actor)).fetchone()
        return row[0] if row else None

    def create_project(self, workspace_id: str, name: str, customer_label: str, by: str) -> Project:
        if self.role(workspace_id, by) not in {"owner", "admin", "contributor"}:
            raise PermissionError("actor cannot create projects")
        created = self._now()
        project = Project(self._id("project", workspace_id, name), workspace_id, name.strip(), customer_label.strip(), "active", created)
        self.db.execute("INSERT OR REPLACE INTO projects(id,workspace_id,name,customer_label,status,created_at) VALUES(?,?,?,?,?,?)", (project.project_id, project.workspace_id, project.name, project.customer_label, project.status, project.created_at))
        self._audit(by, "project_created", project.project_id, {"name": name, "customer_label": customer_label})
        self.db.commit()
        return project

    def add_reviews(self, project_id: str, drafts: Iterable[object], by: str) -> int:
        project = self.db.execute("SELECT workspace_id FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            raise ValueError("unknown project")
        if self.role(project[0], by) not in {"owner", "admin", "contributor"}:
            raise PermissionError("actor cannot add review items")
        count = 0
        for draft in drafts:
            data = asdict(draft) if hasattr(draft, "__dataclass_fields__") else dict(draft)
            item_id = self._id("review", project_id, data["question_id"])
            self.db.execute("INSERT OR REPLACE INTO reviews(id,project_id,question_id,question,category,draft,sources,confidence,review,warning,reviewer,reviewer_note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (item_id, project_id, data["question_id"], data["question"], data["category"], data["draft"], json.dumps(data.get("sources", []), ensure_ascii=False), data["confidence"], data.get("review", "pending_review"), data.get("warning"), None, None))
            count += 1
        self._audit(by, "reviews_imported", project_id, {"count": count})
        self.db.commit()
        return count

    def transition(self, item_id: str, new_state: str, actor: str, note: str | None = None) -> None:
        row = self.db.execute("SELECT project_id, review FROM reviews WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise ValueError("unknown review item")
        project_id, old_state = row
        workspace = self.db.execute("SELECT workspace_id FROM projects WHERE id=?", (project_id,)).fetchone()
        if self.role(workspace[0], actor) not in {"owner", "admin", "reviewer"}:
            raise PermissionError("actor cannot review items")
        if new_state not in _TRANSITIONS.get(old_state, set()):
            raise ValueError(f"invalid review transition: {old_state} -> {new_state}")
        self.db.execute("UPDATE reviews SET review=?, reviewer=?, reviewer_note=? WHERE id=?", (new_state, actor, note, item_id))
        self._audit(actor, "review_transition", item_id, {"from": old_state, "to": new_state, "note": note})
        self.db.commit()

    def list_reviews(self, project_id: str, state: str | None = None) -> list[ReviewItem]:
        query = "SELECT id,project_id,question_id,question,category,draft,sources,confidence,review,warning,reviewer,reviewer_note FROM reviews WHERE project_id=?"
        args: list[str] = [project_id]
        if state:
            query += " AND review=?"
            args.append(state)
        query += " ORDER BY question_id"
        rows = self.db.execute(query, args).fetchall()
        return [ReviewItem(r[0], r[1], r[2], r[3], r[4], r[5], json.loads(r[6]), r[7], r[8], r[9], r[10], r[11]) for r in rows]

    def audit_log(self, target: str | None = None, limit: int = 100) -> list[dict]:
        if target:
            rows = self.db.execute("SELECT actor,action,target,detail,created_at FROM audit WHERE target=? ORDER BY created_at DESC LIMIT ?", (target, max(1, min(limit, 500)))).fetchall()
        else:
            rows = self.db.execute("SELECT actor,action,target,detail,created_at FROM audit ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
        return [{"actor": r[0], "action": r[1], "target": r[2], "detail": json.loads(r[3]), "created_at": r[4]} for r in rows]

    def export_csv(self, project_id: str, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        items = self.list_reviews(project_id)
        with output.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=["question_id", "question", "category", "draft", "sources", "confidence", "review", "warning", "reviewer", "reviewer_note"])
            writer.writeheader()
            for item in items:
                row = asdict(item)
                row["sources"] = " | ".join(item.sources)
                row.pop("item_id")
                row.pop("project_id")
                writer.writerow(row)
