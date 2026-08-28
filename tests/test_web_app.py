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
            response = client.get("/api/search?q=encrypted")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json["results"])
            response = client.post("/ask", data={"question": "Is customer data encrypted at rest?"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Confidence", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
