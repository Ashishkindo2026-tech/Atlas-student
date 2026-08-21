"""Reliable local Ollama client used by Atlas."""
from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from atlas_core.config import CONFIG


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot satisfy a request."""


class Ollama_Client:
    """Defensive, retrying client for Ollama's local HTTP API."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        retries: int = 2,
        num_ctx: int | None = None,
        num_thread: int | None = None,
    ) -> None:
        self.model = (model or CONFIG.ollama_model).strip()
        self.base_url = (base_url or CONFIG.ollama_base_url).rstrip("/")
        self.timeout = timeout if timeout is not None else CONFIG.request_timeout_seconds
        self.retries = retries
        self.num_ctx = num_ctx
        self.num_thread = num_thread
        if not self.model:
            raise ValueError("Ollama model name cannot be empty")
        if self.timeout <= 0:
            raise ValueError("Ollama timeout must be greater than zero")
        if self.retries < 0:
            raise ValueError("Ollama retries cannot be negative")

        retry_policy = Retry(
            total=self.retries,
            connect=self.retries,
            read=self.retries,
            status=self.retries,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            raise_on_status=False,
        )
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=retry_policy))
        self.session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    @property
    def generate_url(self) -> str:
        return f"{self.base_url}/api/generate"

    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=min(self.timeout, 5))
            return response.ok
        except requests.RequestException:
            return False

    def ask(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        options: dict[str, int] = {}
        if self.num_ctx is not None:
            options["num_ctx"] = self.num_ctx
        if self.num_thread is not None:
            options["num_thread"] = self.num_thread
        payload: dict[str, Any] = {"model": self.model, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options

        try:
            response = self.session.post(self.generate_url, json=payload, timeout=self.timeout)
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
        if data.get("error"):
            raise OllamaError(str(data["error"]))
        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaError("Ollama returned no usable response")
        return answer.strip()
