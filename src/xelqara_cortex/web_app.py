from __future__ import annotations

import argparse
import html
import json
import secrets
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template_string

from .core import Cortex
from .bidcore import BidCore

_ALLOWED = {".txt", ".md", ".csv", ".tsv", ".xlsx", ".docx", ".pdf"}

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xelqara BidCore</title>
<style>
:root{color-scheme:dark}body{font-family:Inter,system-ui,sans-serif;max-width:1100px;margin:0 auto;padding:28px 18px;background:#0b1020;color:#eef2ff}header{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid #273252;padding-bottom:22px;margin-bottom:22px}h1{margin:0;font-size:2rem}h2{margin-top:0;color:#c4b5fd}.muted{color:#a5b4fc}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}.panel{background:#151d35;border:1px solid #2d3a5e;border-radius:12px;padding:20px}input,textarea{box-sizing:border-box;width:100%;padding:11px;margin:6px 0 14px;border-radius:7px;border:1px solid #44527d;background:#0f172a;color:#fff}button{padding:11px 17px;border:0;border-radius:7px;background:#7c3aed;color:#fff;font-weight:700;cursor:pointer}.stat{font-size:2rem;color:#a78bfa;font-weight:800}.result{white-space:pre-wrap;background:#0f172a;border-left:3px solid #8b5cf6;padding:15px;line-height:1.55}.badge{display:inline-block;padding:4px 8px;border-radius:20px;background:#26355d;color:#ddd6fe;margin-right:6px}a{color:#c4b5fd}.alert{padding:12px;border-radius:7px;background:#4c1d1d;color:#fecaca;margin:12px 0}
</style></head><body>
<header><div><h1>Xelqara BidCore</h1><div class="muted">Evidence-backed RFP workspace · local-first · no API key</div></div><div class="badge">{{ count }} evidence chunks</div></header>
{% if message %}<div class="panel">{{ message }}</div>{% endif %}
<div class="grid"><section class="panel"><h2>1. Upload evidence</h2><p class="muted">TXT, Markdown, CSV, TSV, XLSX, DOCX, or text PDF. Files remain in this environment.</p><form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data"><input type="file" name="document" required><button>Import document</button></form></section>
<section class="panel"><h2>2. Ask BidCore</h2><form method="post" action="{{ url_for('ask') }}"><textarea name="question" rows="5" placeholder="Do you encrypt customer data at rest?\nهل يتم تشفير بيانات العملاء أثناء التخزين؟" required></textarea><button>Generate evidence draft</button></form></section></div>
{% if draft %}<section class="panel" style="margin-top:18px"><h2>Draft result</h2><p><span class="badge">{{ draft.category }}</span><span class="badge">Confidence: {{ draft.confidence }}</span><span class="badge">{{ draft.review }}</span></p>{% if draft.warning %}<div class="alert">{{ draft.warning }}</div>{% endif %}<div class="result">{{ draft.draft }}</div><p class="muted">Sources: {% for source in draft.sources %}<span class="badge">{{ source }}</span>{% else %}none{% endfor %}</p></section>{% endif %}
<section class="panel" style="margin-top:18px"><h2>Operating policy</h2><p class="muted">BidCore treats document instructions as untrusted data. Unsupported answers stay low-confidence and require human review. Do not expose this development interface beyond localhost without authentication, TLS, backups, and customer security controls.</p></section>
</body></html>"""


def create_app(root: str = ".cortex") -> Flask:
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    inbox = root_path / "inbox"
    inbox.mkdir(exist_ok=True)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
    cortex = Cortex(root_path)

    @app.get("/")
    def home():
        count = len(cortex.search("", limit=500))
        return render_template_string(_PAGE, count=count, draft=None, message=None)

    @app.post("/upload")
    def upload():
        uploaded = request.files.get("document")
        if uploaded is None or not uploaded.filename:
            return redirect(url_for("home"))
        suffix = Path(uploaded.filename).suffix.lower()
        if suffix not in _ALLOWED:
            return render_template_string(_PAGE, count=0, draft=None, message="Unsupported file format."), 400
        safe_name = f"{secrets.token_hex(8)}_{Path(uploaded.filename).name}"
        target = inbox / safe_name
        uploaded.save(target)
        try:
            chunks = cortex.ingest_file(target, logical_name=Path(uploaded.filename).name, replace=True)
            return render_template_string(_PAGE, count=len(cortex.search("", limit=500)), draft=None, message=f"Imported {chunks} evidence chunks from {html.escape(uploaded.filename)}.")
        except Exception as exc:
            return render_template_string(_PAGE, count=0, draft=None, message=f"Import failed: {html.escape(str(exc))}"), 400

    @app.post("/ingest")
    def ingest_legacy():
        path = request.form.get("path", "")
        candidate = Path(path).expanduser().resolve()
        if not candidate.is_file() or candidate.suffix.lower() not in _ALLOWED:
            return render_template_string(_PAGE, count=0, draft=None, message="Invalid or unsupported local file path."), 400
        try:
            chunks = cortex.ingest_file(candidate, logical_name=candidate.name, replace=True)
            return render_template_string(_PAGE, count=len(cortex.search("", limit=500)), draft=None, message=f"Imported {chunks} evidence chunks from {html.escape(candidate.name)}.")
        except Exception as exc:
            return render_template_string(_PAGE, count=0, draft=None, message=f"Import failed: {html.escape(str(exc))}"), 400

    @app.post("/ask")
    def ask():
        question = request.form.get("question", "").strip()
        if not question:
            return redirect(url_for("home"))
        draft = BidCore(cortex).draft(BidCore.parse_questions([question])[0])
        return render_template_string(_PAGE, count=len(cortex.search("", limit=500)), draft=draft, message=None)

    @app.errorhandler(413)
    def too_large(_error):
        return render_template_string(_PAGE, count=0, draft=None, message="File is larger than the 25 MB safety limit."), 413

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
