import unittest
from xelqara_cortex.bidcore import BidCore
from xelqara_cortex.document_io import DocumentChunk


class QuestionExtractionTests(unittest.TestCase):
    def test_extracts_question_and_id_from_table_row(self):
        chunks = [
            DocumentChunk("client.xlsx", "sheet:Questionnaire/row:1", "Question ID | Question | Owner", {"sheet": "Questionnaire", "row": 1}),
            DocumentChunk("client.xlsx", "sheet:Questionnaire/row:2", "SEC-001 | Is MFA enforced for administrators? | Security", {"sheet": "Questionnaire", "row": 2}),
        ]
        questions = BidCore.parse_document_chunks(chunks)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_id, "SEC-001")
        self.assertEqual(questions[0].category, "security")


if __name__ == "__main__":
    unittest.main()
