"""Evidence-grounded RFP and security-questionnaire drafting for Xelqara BidCore."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .core import Cortex, Evidence
from .local_model import LocalModel

_CATEGORIES = {
    "security": re.compile(r"(?i)(security|encrypt|encryption|mfa|sso|identity|access|incident|breach|soc\s*2|iso\s*27001|التشفير|الأمن|الوصول|الحادثة)"),
    "compliance": re.compile(r"(?i)(compliance|gdpr|hipaa|regulat|audit|policy|امتثال|تدقيق|سياسة)"),
    "implementation": re.compile(r"(?i)(implement|deployment|support|sla|timeline|integration|التنفيذ|الدعم|التكامل)"),
    "pricing": re.compile(r"(?i)(price|pricing|cost|license|fee|السعر|التكلفة|الترخيص)"),
}

@dataclass(frozen=True)
class BidQuestion:
    question_id: str
    question: str
    category: str

@dataclass(frozen=True)
class BidDraft:
    question_id: str
    question: str
    category: str
    draft: str
    sources: list[str]
    confidence: str
    review: str
    warning: str | None = None

class BidCore:
    def __init__(self, cortex: Cortex, model: LocalModel | None = None) -> None:
        self.cortex = cortex
        self.model = model

    @staticmethod
    def classify(question: str) -> str:
        for category, pattern in _CATEGORIES.items():
            if pattern.search(question):
                return category
        return "general"

    @classmethod
    def parse_questions(cls, rows: Iterable[str]) -> list[BidQuestion]:
        questions: list[BidQuestion] = []
        for index, row in enumerate(rows, 1):
            text = str(row).strip()
            if text:
                questions.append(BidQuestion(f"Q{index:04d}", text, cls.classify(text)))
        return questions

    @staticmethod
    def _draft(question: str, evidence: list[Evidence]) -> tuple[str, str, str | None]:
        if not evidence:
            return ("لا توجد إجابة معتمدة في قاعدة المعرفة. أضف مصدراً أو أحِل السؤال إلى خبير مختص.", "low", "Unsupported question; human answer required.")
        risky = [item for item in evidence if item.warning]
        if risky:
            return ("تم العثور على نص ذي تحذير أمني؛ لم يتم استخدامه كتعليمات. راجع المصدر يدوياً قبل اعتماد أي إجابة.", "low", "Retrieved content requires manual review.")
        excerpts = []
        for item in evidence[:3]:
            excerpt = re.sub(r"\s+", " ", item.text).strip()[:600]
            excerpts.append(f"[{item.source}] {excerpt}")
        confidence = "high" if len(evidence) >= 2 and evidence[0].score >= 0.5 else "medium"
        return ("مسودة مبنية على مصادر المؤسسة، وتحتاج مراجعة واعتماداً بشرياً:\n" + "\n".join(excerpts), confidence, "Human approval required before submission.")

    def draft(self, question: BidQuestion, evidence_limit: int = 3) -> BidDraft:
        evidence = self.cortex.search(question.question, evidence_limit)
        text, confidence, warning = self._draft(question.question, evidence)
        if self.model is not None and evidence and not any(item.warning for item in evidence):
            context = "\n\n".join(f"SOURCE={item.source}\n{item.text[:1200]}" for item in evidence)
            system = "You draft a factual enterprise RFP answer. Use only the supplied evidence. If evidence is insufficient, say so. Never invent certifications, pricing, legal commitments, or security controls. Return a concise answer for human review."
            prompt = f"Question: {question.question}\nCategory: {question.category}\nEvidence:\n{context}"
            try:
                response = self.model.generate(prompt, system)
                if response.text.strip():
                    text = "مسودة النموذج المحلي المبنية على الأدلة التالية، وتحتاج مراجعة واعتماداً بشرياً:\n" + response.text.strip()
                    confidence = "medium"
                    warning = "Local-model draft; verify every claim against cited sources before submission."
            except Exception as exc:
                warning = f"Local model unavailable; deterministic evidence draft retained: {exc}"
        return BidDraft(question.question_id, question.question, question.category, text, [item.source for item in evidence], confidence, "pending_review", warning)

    def draft_batch(self, questions: Iterable[BidQuestion], evidence_limit: int = 3) -> list[BidDraft]:
        return [self.draft(question, evidence_limit) for question in questions]

    @staticmethod
    def export_json(drafts: Iterable[BidDraft], path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps([asdict(item) for item in drafts], ensure_ascii=False, indent=2), encoding="utf-8")
