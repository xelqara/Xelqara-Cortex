import json
import tempfile
import unittest
from pathlib import Path

from xelqara_cortex import Cortex
from xelqara_cortex.bidcore import BidCore
from xelqara_cortex.enterprise import EnterpriseStore
from xelqara_cortex.trust_pack import build_trust_pack


class TrustPackTests(unittest.TestCase):
    def test_pack_contains_approved_answers_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cortex = Cortex(root)
            store = EnterpriseStore(root)
            try:
                cortex.ingest_text("security.md", "Customer data is encrypted at rest.")
                workspace = store.create_workspace("Demo", "owner")
                project = store.create_project(workspace.workspace_id, "RFP", "Customer", "owner")
                draft = BidCore(cortex).draft(BidCore.parse_questions(["Is customer data encrypted at rest?"])[0])
                store.add_reviews(project.project_id, [draft], "owner")
                item = store.list_reviews(project.project_id)[0]
                store.transition(item.item_id, "in_review", "owner")
                store.transition(item.item_id, "approved", "owner", "verified")
                output = root / "trust-pack.json"
                result = build_trust_pack(cortex, store, project.project_id, output)
                payload = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(result["approved_items"], 1)
                self.assertEqual(payload["coverage"]["pending_or_other_items"], 0)
                self.assertEqual(payload["approved_answers"][0]["review"], "approved")
                self.assertTrue(payload["source_inventory"])
                self.assertTrue(payload["audit"])
            finally:
                store.close()
                cortex.close()


if __name__ == "__main__":
    unittest.main()
