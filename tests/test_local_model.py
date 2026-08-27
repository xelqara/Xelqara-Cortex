import tempfile
import unittest

from xelqara_cortex.bidcore import BidCore
from xelqara_cortex.core import Cortex
from xelqara_cortex.local_model import LocalModelError, ModelResponse


class FakeLocalModel:
    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        self.prompt = prompt
        return ModelResponse("The approved local draft confirms the cited capability.", "fake-local")


class StructuredFake:
    def __init__(self, text):
        self.text = text

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        return ModelResponse(self.text, "fake-structured")


class LocalModelTests(unittest.TestCase):
    def test_structured_output_validation(self):
        from xelqara_cortex.local_model import LocalModel
        model = StructuredFake('{"answer": "ok"}')
        self.assertEqual(LocalModel.generate_structured(model, "question")["answer"], "ok")
        with self.assertRaises(LocalModelError):
            LocalModel.generate_structured(StructuredFake("not-json"), "question")

    def test_model_draft_remains_pending_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cortex = Cortex(tmp)
            cortex.ingest_text("approved.md", "The service supports encrypted storage.")
            draft = BidCore(cortex, model=FakeLocalModel()).draft(BidCore.parse_questions(["Does the service support encrypted storage?"])[0])
            self.assertIn("approved local draft", draft.draft)
            self.assertEqual(draft.review, "pending_review")
            self.assertIn("Local-model draft", draft.warning)
            cortex.close()


if __name__ == "__main__":
    unittest.main()
