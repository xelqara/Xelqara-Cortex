"""Optional local-model adapters for BidCore.

No adapter is enabled by default. OllamaAdapter talks only to a loopback
address and LocalCommandAdapter invokes an explicitly configured executable.
Both are provider-neutral and keep model use separate from evidence policy.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from urllib import request

@dataclass(frozen=True)
class ModelResponse:
    text: str
    model: str
    mode: str = "local"

class LocalModelError(RuntimeError):
    pass

class LocalModel:
    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        raise NotImplementedError

    def generate_structured(self, prompt: str, system: str = "") -> dict:
        response = self.generate(prompt, system)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LocalModelError("local model did not return valid JSON") from exc
        if not isinstance(value, dict):
            raise LocalModelError("local model JSON response must be an object")
        return value

class OllamaAdapter(LocalModel):
    def __init__(self, model: str, endpoint: str = "http://127.0.0.1:11434/api/generate") -> None:
        if not endpoint.startswith("http://127.0.0.1") and not endpoint.startswith("http://localhost"):
            raise ValueError("OllamaAdapter only permits loopback endpoints")
        self.model = model
        self.endpoint = endpoint

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        payload = json.dumps({"model": self.model, "prompt": prompt, "system": system, "stream": False}).encode()
        req = request.Request(self.endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=180) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise LocalModelError(f"local model request failed: {exc}") from exc
        return ModelResponse(str(data.get("response", "")), self.model)

class LocalCommandAdapter(LocalModel):
    def __init__(self, executable: str, model: str = "local-command", extra_args: list[str] | None = None) -> None:
        self.executable = executable
        self.model = model
        self.extra_args = list(extra_args or [])

    def generate(self, prompt: str, system: str = "") -> ModelResponse:
        combined = f"{system}\n\n{prompt}" if system else prompt
        try:
            completed = subprocess.run([self.executable, *self.extra_args], input=combined, text=True, capture_output=True, timeout=180, check=True)
        except Exception as exc:
            raise LocalModelError(f"local command failed: {exc}") from exc
        return ModelResponse(completed.stdout.strip(), self.model)
