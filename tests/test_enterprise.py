import tempfile
import unittest

from xelqara_cortex.bidcore import BidCore
from xelqara_cortex.core import Cortex
from xelqara_cortex.enterprise import EnterpriseStore


class EnterpriseTests(unittest.TestCase):
    def test_workspace_project_review_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            store = EnterpriseStore(tmp)
            workspace = store.create_workspace("Acme Bid Team", "owner")
            store.add_member(workspace.workspace_id, "reviewer", "reviewer", "owner")
            project = store.create_project(workspace.workspace_id, "Q3 Security RFP", "Acme customer", "owner")
            cortex.ingest_text("security.md", "The service encrypts data at rest and in transit.")
            drafts = BidCore(cortex).draft_batch(BidCore.parse_questions(["Do you encrypt data at rest?"]))
            self.assertEqual(store.add_reviews(project.project_id, drafts, "owner"), 1)
            item = store.list_reviews(project.project_id)[0]
            self.assertEqual(item.review, "pending_review")
            store.transition(item.item_id, "in_review", "reviewer", "Checking source")
            store.transition(item.item_id, "approved", "reviewer", "Evidence confirmed")
            store.export_csv(project.project_id, f"{tmp}/export.csv")
            self.assertIn("approved", open(f"{tmp}/export.csv", encoding="utf-8-sig").read())
            self.assertTrue(store.audit_log(project.project_id))
            store.close()
            cortex.close()

    def test_rejects_unauthorized_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            store = EnterpriseStore(tmp)
            workspace = store.create_workspace("Team", "owner")
            project = store.create_project(workspace.workspace_id, "RFP", "Client", "owner")
            drafts = BidCore(cortex).draft_batch(BidCore.parse_questions(["Unsupported question?"]))
            store.add_reviews(project.project_id, drafts, "owner")
            item = store.list_reviews(project.project_id)[0]
            with self.assertRaises(PermissionError):
                store.transition(item.item_id, "in_review", "stranger")
            store.close()
            cortex.close()


if __name__ == "__main__":
    unittest.main()
