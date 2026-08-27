import csv
import tempfile
import unittest
from pathlib import Path

from xelqara_cortex.core import Cortex
from xelqara_cortex.document_io import DocumentImporter


class DocumentIOTests(unittest.TestCase):
    def test_csv_preserves_row_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "questions.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["Question ID", "Question", "Owner"])
                writer.writerow(["SEC-001", "Is MFA enforced?", "Security"])
            chunks = DocumentImporter().import_file(path)
            self.assertEqual(chunks[1].location, "row:2")
            self.assertIn("MFA", chunks[1].text)

    def test_xlsx_ingestion_preserves_sheet_and_row(self):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("openpyxl not installed")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "questions.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Questionnaire"
            sheet.append(["Question ID", "Question"])
            sheet.append(["SEC-001", "Is customer data encrypted?"])
            workbook.save(path)
            chunks = DocumentImporter().import_file(path)
            self.assertEqual(chunks[1].location, "sheet:Questionnaire/row:2")
            cortex = Cortex(Path(tmp) / "db")
            self.assertEqual(cortex.ingest_file(path, logical_name="client.xlsx"), 2)
            evidence = cortex.search("customer data encrypted")
            self.assertEqual(evidence[0].source, "client.xlsx")
            self.assertEqual(evidence[0].location, "sheet:Questionnaire/row:2")
            cortex.close()


if __name__ == "__main__":
    unittest.main()
