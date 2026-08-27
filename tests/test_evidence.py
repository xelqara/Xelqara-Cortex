import tempfile
import unittest

from xelqara_cortex.evidence import EvidenceRegistry


class EvidenceTests(unittest.TestCase):
    def test_register_and_find_stale_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = EvidenceRegistry(tmp)
            record = registry.register("security-policy.md", "security", "confidential", "approved", "2026-01-01", "2026-02-01")
            self.assertEqual(registry.get("security-policy.md"), record)
            self.assertEqual(registry.stale("2026-03-01T00:00:00+00:00")[0].source, "security-policy.md")
            registry.close()

    def test_rejects_invalid_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = EvidenceRegistry(tmp)
            with self.assertRaises(ValueError):
                registry.register("policy.md", "owner", approval="made_up")
            registry.close()


if __name__ == "__main__":
    unittest.main()
