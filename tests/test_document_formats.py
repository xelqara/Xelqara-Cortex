import tempfile
import unittest
import zipfile
from pathlib import Path

from xelqara_cortex.document_io import DocumentImporter, DocumentImportError


class DocumentFormatTests(unittest.TestCase):
    def test_docx_paragraph_locations(self):
        xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Security policy paragraph.</w:t></w:r></w:p><w:p><w:r><w:t>MFA is required.</w:t></w:r></w:p></w:body></w:document>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.docx"
            with zipfile.ZipFile(path, "w") as package:
                package.writestr("word/document.xml", xml)
            chunks = DocumentImporter().import_file(path)
            self.assertEqual(chunks[1].location, "paragraph:2")
            self.assertIn("MFA", chunks[1].text)

    def test_pdf_adapter_reports_missing_binary_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.pdf"
            path.write_bytes(b"not a real pdf")
            try:
                chunks = DocumentImporter().import_file(path)
            except DocumentImportError:
                return
            self.assertIsInstance(chunks, list)


if __name__ == "__main__":
    unittest.main()
