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
