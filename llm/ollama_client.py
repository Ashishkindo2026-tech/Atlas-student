"""Reliable local Ollama client used by Atlas.

The client is deliberately small and dependency-light, but it treats HTTP
failures and malformed responses as first-class errors instead of silently
turning them into model output.
"""

from __future__ import annotations

import os
from typing import Any

import requests


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot satisfy a request."""


class Ollama_Client:
    """Small, defensive client for Ollama's /api/generate endpoint."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.model = (model or os.getenv("ATLAS_OLLAMA_MODEL") or "qwen2.5:1.5b").strip()
        self.base_url = (base_url or os.getenv("ATLAS_OLLAMA_URL") or "http://localhost:11434").rstrip("/")
        self.timeout = timeout if timeout is not None else float(os.getenv("ATLAS_OLLAMA_TIMEOUT", "120"))
        if not self.model:
            raise ValueError("Ollama model name cannot be empty")
        if self.timeout <= 0:
            raise ValueError("Ollama timeout must be greater than zero")

    @property
    def generate_url(self) -> str:
        return f"{self.base_url}/api/generate"

    def health_check(self) -> bool:
        """Return True when Ollama responds to its version endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=min(self.timeout, 5))
            return response.ok
        except requests.RequestException:
            return False

    def ask(self, prompt: str) -> str:
        """Generate a response, raising OllamaError on infrastructure failure."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        try:
            response = requests.post(
                self.generate_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise OllamaError(f"Ollama request timed out after {self.timeout:g}s") from exc
        except requests.ConnectionError as exc:
            raise OllamaError("Ollama is unavailable at " + self.base_url) from exc
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama HTTP request failed: {exc}") from exc

        try:
            data: Any = response.json()
        except ValueError as exc:
            raise OllamaError("Ollama returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise OllamaError("Ollama returned an invalid response object")

        error = data.get("error")
        if error:
            raise OllamaError(str(error))

        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaError("Ollama returned no usable response")

        return answer.strip()
