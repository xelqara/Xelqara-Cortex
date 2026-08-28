from __future__ import annotations

import argparse
import secrets
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from .bidcore import BidCore
from .core import Cortex

_ALLOWED = {".txt", ".md", ".csv", ".tsv", ".xlsx", ".docx", ".pdf"}

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xelqara BidCore | Private RFP Review</title>
<style>
:root{color-scheme:dark;--bg:#080b14;--surface:#111827;--surface2:#172033;--line:#28344d;--text:#f8fafc;--muted:#94a3b8;--accent:#8b5cf6;--accent2:#c4b5fd;--good:#34d399;--warn:#fbbf24}
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;max-width:1180px;margin:0 auto;padding:32px 20px;background:radial-gradient(circle at 85% 0,#1e1745 0,transparent 35%),var(--bg);color:var(--text);line-height:1.5}header{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:24px}h1{margin:0;font-size:clamp(2rem,4vw,3.2rem);letter-spacing:-.04em}h2{margin:0 0 10px;font-size:1.05rem;letter-spacing:.01em}.eyebrow{color:var(--accent2);font-size:.78rem;text-transform:uppercase;letter-spacing:.18em;font-weight:800}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}.panel{background:linear-gradient(145deg,rgba(23,32,51,.96),rgba(15,23,42,.96));border:1px solid var(--line);border-radius:14px;padding:22px}.span-7{grid-column:span 7}.span-5{grid-column:span 5}.span-12{grid-column:span 12}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:22px 0}.stat{padding:15px 16px;background:rgba(8,11,20,.55);border:1px solid var(--line);border-radius:10px}.stat strong{display:block;font-size:1.65rem;color:var(--accent2)}.stat span{font-size:.78rem;color:var(--muted)}input,textarea{width:100%;padding:12px 13px;margin:8px 0 14px;border-radius:9px;border:1px solid #3b4967;background:#0b1220;color:var(--text);font:inherit}input:focus,textarea:focus{outline:2px solid var(--accent);outline-offset:1px}button{padding:12px 17px;border:0;border-radius:9px;background:var(--accent);color:white;font-weight:800;cursor:pointer}button.secondary{background:#273451;color:#ddd6fe}.badge{display:inline-block;padding:4px 9px;border-radius:999px;background:#26355d;color:#ddd6fe;margin:2px 5px 2px 0;font-size:.78rem}.result{white-space:pre-wrap;background:#0a1020;border:1px solid #34415f;border-radius:10px;padding:16px;line-height:1.65}.alert{padding:12px;border-radius:9px;background:#3b1d22;color:#fecaca;margin:14px 0;border:1px solid #7f1d1d}.notice{padding:13px 15px;border-left:3px solid var(--good);background:rgba(6,78,59,.2);color:#bbf7d0;border-radius:4px}.footer{margin-top:22px;padding-top:16px;border-top:1px solid var(--line);font-size:.85rem}.small{font-size:.88rem}@media(max-width:760px){header{display:block}.span-7,.span-5,.span-12{grid-column:span 12}.stats{grid-template-columns:1fr 1fr 1fr}.panel{padding:17px}}
</style></head><body>
<header><div><div class="eyebrow">Xelqara AI · Project 01</div><h1>BidCore</h1><div class="muted">Private, evidence-grounded RFP and security questionnaire review.</div></div><div class="badge">LOCAL-FIRST · NO API KEY</div></header>
<div class="stats"><div class="stat"><strong>{{ count }}</strong><span>Evidence chunks</span></div><div class="stat"><strong>{{ sources }}</strong><span>Source documents</span></div><div class="stat"><strong>100%</strong><span>Human approval required</span></div></div>
{% if message %}<div class="notice">{{ message }}</div>{% endif %}
<div class="grid" style="margin-top:16px"><section class="panel span-5"><div class="eyebrow">01 · Evidence base</div><h2>Import approved company knowledge</h2><p class="muted small">Supported: TXT, Markdown, CSV, TSV, XLSX, DOCX, and text PDF. Files remain in this local environment and are never sent to an external provider.</p><form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data"><input type="file" name="document" accept=".txt,.md,.csv,.tsv,.xlsx,.docx,.pdf" required><button>Import evidence</button></form></section>
<section class="panel span-7"><div class="eyebrow">02 · Review workflow</div><h2>Ask one RFP or security question</h2><p class="muted small">BidCore retrieves relevant evidence, drafts a conservative answer, cites sources, and keeps the result in <b>pending_review</b>.</p><form method="post" action="{{ url_for('ask') }}"><textarea name="question" rows="4" placeholder="Do you encrypt customer data at rest?\nهل يتم تشفير بيانات العملاء أثناء التخزين؟" required></textarea><button>Generate evidence draft</button></form></section></div>
{% if draft %}<section class="panel span-12" style="margin-top:16px"><div class="eyebrow">Review output</div><h2>Draft answer</h2><p><span class="badge">{{ draft.category }}</span><span class="badge">Confidence: {{ draft.confidence }}</span><span class="badge">{{ draft.review }}</span></p>{% if draft.warning %}<div class="alert">{{ draft.warning }}</div>{% endif %}<div class="result">{{ draft.draft }}</div><p class="muted small">Sources: {% for source in draft.sources %}<span class="badge">{{ source }}</span>{% else %}none{% endfor %}</p></section>{% endif %}
<section class="panel span-12" style="margin-top:16px"><div class="eyebrow">03 · Pre-flight coverage</div><h2>Check coverage before committing to an RFP</h2><p class="muted small">Paste one question per line. A weak keyword overlap is not treated as reliable support; the report is a conservative preparation heuristic.</p><form method="post" action="{{ url_for('coverage') }}"><textarea name="questions" rows="5" placeholder="Do you encrypt customer data at rest?\nWhat is your disaster recovery RTO?\nDescribe your incident response process."></textarea><button class="secondary">Analyze coverage</button></form>{% if report %}<p><span class="badge">{{ report.total_questions }} questions</span><span class="badge">{{ report.supported_questions }} supported</span><span class="badge">{{ report.gap_questions }} gaps</span><span class="badge">Recommendation: {{ report.recommendation }}</span></p>{% for category, values in report.by_category.items() %}<span class="badge">{{ category }} · {{ values.supported }}/{{ values.total }}</span>{% endfor %}{% endif %}</section>
<section class="panel span-12" style="margin-top:16px"><div class="eyebrow">Operating boundary</div><h2>Designed for accountable enterprise review</h2><p class="muted small">Document text is treated as untrusted data. Unsupported questions remain low-confidence. BidCore does not invent certifications, pricing, legal commitments, or security controls. Do not expose this development interface beyond localhost without customer authentication, TLS, backups, and a deployment security review.</p></section>
<div class="footer muted">Xelqara BidCore is a drafting and evidence-review system, not an autonomous submission service or a certification.</div>
</body></html>"""


def _stats(cortex: Cortex) -> tuple[int, int]:
    row = cortex.db.execute("SELECT COUNT(*), COUNT(DISTINCT source) FROM chunks").fetchone()
    return int(row[0]), int(row[1])


def _render(cortex: Cortex, **kwargs):
    count, sources = _stats(cortex)
    kwargs.setdefault("report", None)
    return render_template_string(_PAGE, count=count, sources=sources, **kwargs)


def _safe_limit(value: object, default: int = 5, maximum: int = 20) -> int:
    try:
        return max(1, min(int(value), maximum))
    except (TypeError, ValueError):
        return default


def create_app(root: str = ".cortex") -> Flask:
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    inbox = root_path / "inbox"
    inbox.mkdir(exist_ok=True)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
    cortex = Cortex(root_path)

    @app.get("/health")
    def health():
        count, sources = _stats(cortex)
        return jsonify({"status": "ok", "service": "xelqara-bidcore", "mode": "local-first", "evidence_chunks": count, "source_documents": sources})

    @app.get("/api/stats")
    def api_stats():
        count, sources = _stats(cortex)
        return jsonify({"evidence_chunks": count, "source_documents": sources, "review_policy": "human_approval_required"})

    @app.get("/api/sources")
    def api_sources():
        return jsonify({"sources": cortex.source_inventory()})

    @app.get("/api/search")
    def api_search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"error": "q is required"}), 400
        results = cortex.search(query, limit=_safe_limit(request.args.get("limit")))
        return jsonify({"query": query, "results": [{"source": item.source, "location": item.location, "score": item.score, "text": item.text, "warning": item.warning} for item in results]})

    @app.post("/api/draft")
    def api_draft():
        payload = request.get_json(silent=True) or {}
        question = str(payload.get("question", "")).strip()
        if not question or len(question) > 4000:
            return jsonify({"error": "question is required and must be under 4000 characters"}), 400
        item = BidCore(cortex).draft(BidCore.parse_questions([question])[0], _safe_limit(payload.get("evidence_limit"), 3, 5))
        return jsonify({"question_id": item.question_id, "question": item.question, "category": item.category, "draft": item.draft, "sources": item.sources, "confidence": item.confidence, "review": item.review, "warning": item.warning})

    @app.post("/api/coverage")
    def api_coverage():
        payload = request.get_json(silent=True) or {}
        rows = payload.get("questions")
        if not isinstance(rows, list) or not rows or len(rows) > 500:
            return jsonify({"error": "questions must be a non-empty JSON list with at most 500 items"}), 400
        questions = BidCore.parse_questions(rows)
        if not questions:
            return jsonify({"error": "questions list contains no usable text"}), 400
        report = BidCore(cortex).coverage_report(questions, _safe_limit(payload.get("evidence_limit"), 3, 5))
        return jsonify(report)

    @app.get("/")
    def home():
        return _render(cortex, draft=None, message=None)

    @app.post("/upload")
    def upload():
        uploaded = request.files.get("document")
        if uploaded is None or not uploaded.filename:
            return _render(cortex, draft=None, message="Choose a document to import."), 400
        suffix = Path(uploaded.filename).suffix.lower()
        if suffix not in _ALLOWED:
            return _render(cortex, draft=None, message="Unsupported file format."), 400
        safe_name = f"{secrets.token_hex(8)}_{Path(uploaded.filename).name}"
        target = inbox / safe_name
        uploaded.save(target)
        try:
            chunks = cortex.ingest_file(target, logical_name=Path(uploaded.filename).name, replace=True)
            return _render(cortex, draft=None, message=f"Imported {chunks} evidence chunks from {Path(uploaded.filename).name}.")
        except Exception as exc:
            return _render(cortex, draft=None, message=f"Import failed: {exc}"), 400

    @app.post("/ingest")
    def ingest_legacy():
        path = request.form.get("path", "")
        candidate = Path(path).expanduser().resolve()
        if not candidate.is_file() or candidate.suffix.lower() not in _ALLOWED:
            return _render(cortex, draft=None, message="Invalid or unsupported local file path."), 400
        try:
            chunks = cortex.ingest_file(candidate, logical_name=candidate.name, replace=True)
            return _render(cortex, draft=None, message=f"Imported {chunks} evidence chunks from {candidate.name}.")
        except Exception as exc:
            return _render(cortex, draft=None, message=f"Import failed: {exc}"), 400

    @app.post("/coverage")
    def coverage():
        raw_questions = request.form.get("questions", "")
        rows = [line.strip() for line in raw_questions.splitlines() if line.strip()]
        if not rows:
            return _render(cortex, draft=None, report=None, message="Add at least one question for coverage analysis."), 400
        if len(rows) > 500:
            return _render(cortex, draft=None, report=None, message="Coverage analysis is limited to 500 questions."), 400
        report = BidCore(cortex).coverage_report(BidCore.parse_questions(rows))
        return _render(cortex, draft=None, report=report, message=None)

    @app.post("/ask")
    def ask():
        question = request.form.get("question", "").strip()
        if not question:
            return redirect(url_for("home"))
        draft = BidCore(cortex).draft(BidCore.parse_questions([question])[0])
        return _render(cortex, draft=draft, message=None)

    @app.errorhandler(413)
    def too_large(_error):
        return _render(cortex, draft=None, message="File is larger than the 25 MB interface limit."), 413

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local BidCore review interface")
    parser.add_argument("--root", default=".cortex")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    create_app(args.root).run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
