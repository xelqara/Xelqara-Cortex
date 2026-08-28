import io
import tempfile
import unittest
from pathlib import Path

try:
    from xelqara_cortex.web_app import create_app
except ImportError:
    create_app = None


class WebAppTests(unittest.TestCase):
    def test_home_and_question_flow(self):
        if create_app is None:
            self.skipTest("Flask is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(tmp)
            client = app.test_client()
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(client.get("/health").json["status"], "ok")
            self.assertEqual(client.get("/api/search").status_code, 400)
            source = Path(tmp) / "knowledge.md"
            source.write_text("Customer data is encrypted at rest.", encoding="utf-8")
            response = client.post("/ingest", data={"path": str(source)})
            self.assertEqual(response.status_code, 200)
            response = client.post("/upload", data={"document": (io.BytesIO(b"MFA is required for admin access."), "security.md")}, content_type="multipart/form-data")
            self.assertEqual(response.status_code, 200)
            response = client.get("/api/search?q=encrypted")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json["results"])
            stats = client.get("/api/stats")
            self.assertEqual(stats.status_code, 200)
            self.assertGreater(stats.json["evidence_chunks"], 0)
            self.assertEqual(stats.json["review_policy"], "human_approval_required")
            sources = client.get("/api/sources")
            self.assertEqual(sources.status_code, 200)
            self.assertEqual(sources.json["sources"][0]["source"], "knowledge.md")
            self.assertGreater(sources.json["sources"][0]["chunks"], 0)
            response = client.post("/api/draft", json={"question": "Is customer data encrypted at rest?"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["review"], "pending_review")
            self.assertIn("sources", response.json)
            response = client.post("/api/coverage", json={"questions": [
                {"id": "SEC-1", "question": "Is customer data encrypted at rest?"},
                {"id": "BCP-1", "question": "What is your disaster recovery RTO?"},
            ]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["total_questions"], 2)
            self.assertEqual(response.json["gap_questions"], 1)
            self.assertEqual(response.json["recommendation"], "review_gaps_before_commitment")
            response = client.post("/ask", data={"question": "Is customer data encrypted at rest?"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Confidence", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
