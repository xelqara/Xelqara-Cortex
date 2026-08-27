from __future__ import annotations

import argparse
import html
from pathlib import Path
from flask import Flask, request, redirect, url_for

from .core import Cortex
from .bidcore import BidCore


def create_app(root: str = ".cortex") -> Flask:
    app = Flask(__name__)
    cortex = Cortex(root)

    @app.get("/")
    def home():
        return """<!doctype html><meta charset='utf-8'><title>Xelqara BidCore</title>
        <style>body{font-family:system-ui;max-width:960px;margin:40px auto;padding:0 18px;background:#111827;color:#f3f4f6}textarea,input{width:100%;padding:10px;margin:6px 0 14px;background:#1f2937;color:#fff;border:1px solid #4b5563}button{padding:10px 16px;background:#8b5cf6;color:white;border:0;border-radius:6px}section{background:#1f2937;padding:18px;margin:18px 0;border-radius:8px}small{color:#c4b5fd}</style>
        <h1>Xelqara BidCore</h1><small>Local-first RFP evidence workspace — no API key</small>
        <section><h2>Ingest a document</h2><form method='post' action='/ingest'><input name='path' placeholder='Path to TXT/MD/CSV/XLSX/DOCX/PDF' required><button>Ingest</button></form></section>
        <section><h2>Ask a question</h2><form method='post' action='/ask'><textarea name='question' rows='4' placeholder='Do you encrypt customer data at rest?' required></textarea><button>Draft answer</button></form></section>"""

    @app.post("/ingest")
    def ingest():
        path = request.form.get("path", "")
        try:
            count = cortex.ingest_file(path, logical_name=Path(path).name, replace=True)
            return f"<p>Ingested {count} chunks from {html.escape(path)}.</p><p><a href='/'>Back</a></p>"
        except Exception as exc:
            return f"<p>Ingestion failed: {html.escape(str(exc))}</p><p><a href='/'>Back</a></p>", 400

    @app.post("/ask")
    def ask():
        question = request.form.get("question", "")
        draft = BidCore(cortex).draft(BidCore.parse_questions([question])[0])
        sources = "".join(f"<li>{html.escape(source)}</li>" for source in draft.sources)
        return f"<h1>Draft</h1><p><b>Category:</b> {html.escape(draft.category)}</p><pre>{html.escape(draft.draft)}</pre><p><b>Confidence:</b> {html.escape(draft.confidence)}</p><p><b>Review:</b> {html.escape(draft.review)}</p><p><b>Sources:</b></p><ul>{sources}</ul><p><a href='/'>Back</a></p>"

    @app.teardown_appcontext
    def close(_error=None):
        pass

    return app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".cortex")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    create_app(args.root).run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
