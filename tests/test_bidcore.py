import tempfile
import unittest

from xelqara_cortex import Cortex
from xelqara_cortex.bidcore import BidCore


class BidCoreTests(unittest.TestCase):
    def test_classifies_security_question(self):
        self.assertEqual(BidCore.classify("Do you support encryption at rest?"), "security")

    def test_drafts_with_sources_and_pending_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            cortex.ingest_text("security.md", "Our service encrypts customer data at rest and in transit.")
            bid = BidCore(cortex)
            question = bid.parse_questions(["Do you encrypt customer data?"])[0]
            draft = bid.draft(question)
            self.assertEqual(draft.review, "pending_review")
            self.assertIn("security.md", draft.sources)
            self.assertIn("customer data", draft.draft)
            cortex.close()

    def test_structured_question_rows_keep_ids(self):
        rows = [{"id": "SEC-7", "question": "Is MFA required for administrators?"}]
        parsed = BidCore.parse_questions(rows)
        self.assertEqual(parsed[0].question_id, "SEC-7")
        self.assertEqual(parsed[0].category, "security")

    def test_coverage_report_surfaces_gaps_before_commitment(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            cortex.ingest_text("security.md", "Customer data is encrypted at rest and MFA protects admin access.")
            report = BidCore(cortex).coverage_report(BidCore.parse_questions([
                "Is customer data encrypted at rest?",
                "What is your disaster recovery RTO?",
            ]))
            self.assertEqual(report["total_questions"], 2)
            self.assertEqual(report["supported_questions"], 1)
            self.assertEqual(report["gap_questions"], 1)
            self.assertEqual(report["recommendation"], "review_gaps_before_commitment")
            cortex.close()

    def test_unsupported_question_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            bid = BidCore(cortex)
            question = bid.parse_questions(["What is your disaster recovery RTO?"])[0]
            draft = bid.draft(question)
            self.assertEqual(draft.confidence, "low")
            self.assertIn("لا توجد إجابة معتمدة", draft.draft)
            self.assertEqual(draft.sources, [])
            cortex.close()


if __name__ == "__main__":
    unittest.main()
