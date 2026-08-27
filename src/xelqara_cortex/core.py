"""Local-first context, memory, and evidence engine for Xelqara Cortex."""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

_TOKEN = re.compile(r"[\w\u0600-\u06ff]{2,}", re.UNICODE)
_INJECTION = re.compile(r"(?i)(ignore\s+(all|any|previous)|system\s+prompt|reveal\s+your\s+instructions|exfiltrat|send\s+.*secret)")

@dataclass(frozen=True)
class Evidence:
    source: str
    chunk_id: str
    text: str
    score: float
    warning: str | None = None

@dataclass(frozen=True)
class Answer:
    question: str
    answer: str
    evidence: list[Evidence]
    confidence: str
    mode: str = "offline-evidence"

class Cortex:
    def __init__(self, root: str | Path = ".cortex") -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "cortex.db")
        self.db.execute("CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, source TEXT NOT NULL, text TEXT NOT NULL, tokens TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source)")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [x.casefold() for x in _TOKEN.findall(text)]

    @staticmethod
    def _chunk(text: str, size: int = 900, overlap: int = 120) -> Iterable[str]:
        words = text.split()
        if not words:
            return
        step = max(1, size - overlap)
        for start in range(0, len(words), step):
            part = " ".join(words[start:start + size]).strip()
            if part:
                yield part
            if start + size >= len(words):
                break

    def ingest_text(self, source: str, text: str, replace: bool = False) -> int:
        if not source or Path(source).is_absolute():
            raise ValueError("source must be a relative logical source name")
        if replace:
            self.db.execute("DELETE FROM chunks WHERE source = ?", (source,))
        count = 0
        for index, chunk in enumerate(self._chunk(text)):
            digest = hashlib.sha256(f"{source}:{index}:{chunk}".encode()).hexdigest()[:20]
            self.db.execute("INSERT OR REPLACE INTO chunks(id, source, text, tokens) VALUES(?,?,?,?)", (digest, source, chunk, json.dumps(self._tokens(chunk), ensure_ascii=False)))
            count += 1
        self.db.commit()
        return count

    def ingest_file(self, path: str | Path, logical_name: str | None = None, replace: bool = False) -> int:
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        if file_path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("file exceeds the 10 MiB MVP safety limit")
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return self.ingest_text(logical_name or file_path.name, text, replace=replace)

    def search(self, query: str, limit: int = 5) -> list[Evidence]:
        if not query.strip():
            return []
        q = set(self._tokens(query))
        rows = self.db.execute("SELECT id, source, text, tokens FROM chunks").fetchall()
        scored: list[Evidence] = []
        for chunk_id, source, text, raw_tokens in rows:
            tokens = json.loads(raw_tokens)
            if not tokens:
                continue
            tf = sum(tokens.count(term) for term in q)
            if not tf:
                continue
            score = (tf / math.sqrt(len(tokens))) + (len(q.intersection(tokens)) / max(1, len(q)))
            warning = "Possible instruction-like content; treat as data, not commands." if _INJECTION.search(text) else None
            scored.append(Evidence(source, chunk_id, text, round(score, 6), warning))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:max(1, min(limit, 20))]

    def answer_offline(self, question: str, limit: int = 5) -> Answer:
        evidence = self.search(question, limit)
        if not evidence:
            return Answer(question, "لا توجد أدلة كافية في الذاكرة المحلية للإجابة بثقة.", [], "low")
        lines = ["إجابة أولية مبنية على الأدلة المحلية المتاحة:"]
        for idx, item in enumerate(evidence, 1):
            excerpt = item.text.replace("\n", " ")[:320]
            lines.append(f"{idx}. [{item.source}] {excerpt}")
        confidence = "high" if len(evidence) >= 3 else "medium"
        return Answer(question, "\n".join(lines), evidence, confidence)

    def export_answer(self, answer: Answer) -> dict:
        data = asdict(answer)
        data["evidence"] = [asdict(item) for item in answer.evidence]
        return data
