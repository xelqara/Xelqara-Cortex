"""Conservative DOCX response writer that preserves the source package."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .bidcore import BidCore, BidDraft
from .core import Cortex
from .document_io import DocumentImporter

_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", _NS)

def _norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

class DocxResponseError(RuntimeError):
    pass

class DocxResponseWriter:
    """Insert reviewable answer paragraphs after matching question paragraphs."""

    def write(self, source: str | Path, output: str | Path, drafts: Iterable[BidDraft]) -> dict[str, object]:
        source_path = Path(source).expanduser().resolve()
        output_path = Path(output).expanduser().resolve()
        if source_path.suffix.lower() != ".docx" or output_path.suffix.lower() != ".docx":
            raise DocxResponseError("source and output must both be .docx files")
        if source_path == output_path:
            raise DocxResponseError("refusing to overwrite the source document")
        draft_map = {_norm(draft.question): draft for draft in drafts}
        with zipfile.ZipFile(source_path, "r") as package:
            try:
                document_xml = package.read("word/document.xml")
            except KeyError as exc:
                raise DocxResponseError("invalid DOCX package") from exc
            root = ET.fromstring(document_xml)
            paragraphs = root.findall(f".//{{{_NS}}}p")
            # ElementTree has no parent pointers; rebuild the body children in place.
            body = root.find(f".//{{{_NS}}}body")
            if body is None:
                raise DocxResponseError("DOCX document body is missing")
            children = list(body)
            matched = 0
            additions: list[ET.Element] = []
            for child in children:
                additions.append(child)
                if child.tag == f"{{{_NS}}}p":
                    text = "".join(node.text or "" for node in child.findall(f".//{{{_NS}}}t"))
                    draft = draft_map.get(_norm(text))
                    if draft is not None:
                        matched += 1
                        response = f"Xelqara Draft ({draft.confidence}; {draft.review}): {draft.draft} | Sources: {', '.join(draft.sources) or 'none'}"
                        new_paragraph = ET.Element(f"{{{_NS}}}p")
                        run = ET.SubElement(new_paragraph, f"{{{_NS}}}r")
                        node = ET.SubElement(run, f"{{{_NS}}}t")
                        node.text = response
                        additions.append(new_paragraph)
            body[:] = additions
            updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output_path, "w") as target:
                for item in package.infolist():
                    target.writestr(item, updated_xml if item.filename == "word/document.xml" else package.read(item.filename))
        return {"source": str(source_path), "output": str(output_path), "matched": matched, "written": matched, "drafts": len(draft_map), "policy": "Drafts require human approval before submission."}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bidcore-fill-docx", description="Fill a copy of a DOCX questionnaire with BidCore drafts")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--root", default=".cortex")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args(argv)
    cortex = Cortex(args.root)
    try:
        chunks = DocumentImporter().import_file(args.input)
        drafts = BidCore(cortex).draft_batch(BidCore.parse_document_chunks(chunks), max(1, min(args.limit, 5)))
        print(json.dumps(DocxResponseWriter().write(args.input, args.output, drafts), ensure_ascii=False, indent=2))
        return 0
    finally:
        cortex.close()

if __name__ == "__main__":
    raise SystemExit(main())
