import tempfile
import unittest
import zipfile
from pathlib import Path

from xelqara_cortex import Cortex
from xelqara_cortex.bidcore import BidCore
from xelqara_cortex.docx_response import DocxResponseWriter
from xelqara_cortex.document_io import DocumentImporter

_DOCUMENT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Do you encrypt customer data at rest?</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'''


class DocxResponseTests(unittest.TestCase):
    def test_preserves_source_and_inserts_reviewable_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "questionnaire.docx"
            output = root / "answered.docx"
            with zipfile.ZipFile(source, "w") as package:
                package.writestr("word/document.xml", _DOCUMENT)
            cortex = Cortex(root / ".cortex")
            try:
                cortex.ingest_text("security.md", "Customer data is encrypted at rest.")
                chunks = DocumentImporter().import_file(source)
                drafts = BidCore(cortex).draft_batch(BidCore.parse_document_chunks(chunks))
                result = DocxResponseWriter().write(source, output, drafts)
                self.assertEqual(result["matched"], 1)
                self.assertTrue(source.exists() and output.exists())
                with zipfile.ZipFile(output) as package:
                    text = package.read("word/document.xml").decode("utf-8")
                self.assertIn("Xelqara Draft", text)
                self.assertIn("security.md", text)
            finally:
                cortex.close()


if __name__ == "__main__":
    unittest.main()
