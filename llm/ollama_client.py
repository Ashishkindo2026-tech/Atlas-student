import os
import time

import requests


class OllamaError(RuntimeError):
    """Base error for Ollama availability or response failures."""


class OllamaUnavailableError(OllamaError):
    """Raised when the Ollama service cannot be reached."""


class OllamaModelError(OllamaError):
    """Raised when the configured model is unavailable or invalid."""


class Ollama_Client:
    """Small, resilient Ollama client used by Atlas.

    The client keeps network concerns in one place so the rest of Atlas does
    not need to know about Ollama's HTTP API. Configuration can be overridden
    with ATLAS_OLLAMA_URL, ATLAS_OLLAMA_MODEL and ATLAS_OLLAMA_TIMEOUT.
    """

    def __init__(self, model=None, base_url=None, timeout=None, retries=2):
        self.base_url = (base_url or os.getenv("ATLAS_OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("ATLAS_OLLAMA_MODEL", "qwen2.5:1.5b")
        self.timeout = float(timeout or os.getenv("ATLAS_OLLAMA_TIMEOUT", "120"))
        self.retries = max(0, int(retries))
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"

    def health_check(self):
        """Return True when the Ollama service itself is reachable."""
        try:
            response = requests.get(self.base_url, timeout=min(self.timeout, 5))
            return response.ok
        except requests.RequestException:
            return False

    def model_available(self):
        """Return True when the configured model is listed by Ollama."""
        try:
            response = requests.get(self.tags_url, timeout=min(self.timeout, 5))
            response.raise_for_status()
            models = response.json().get("models", [])
            names = {str(item.get("name", "")) for item in models if isinstance(item, dict)}
            return self.model in names
        except (requests.RequestException, ValueError, TypeError):
            return False

    def status(self):
        """Return a diagnostic snapshot without raising network errors."""
        service = self.health_check()
        return {
            "service": service,
            "model": self.model,
            "model_available": self.model_available() if service else False,
            "url": self.base_url,
        }

    def _request(self, prompt):
        response = requests.post(
            self.generate_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise OllamaError("Ollama returned invalid JSON.") from exc

        result = data.get("response") if isinstance(data, dict) else None
        if not isinstance(result, str) or not result.strip():
            raise OllamaError("Ollama returned an empty response.")
        return result.strip()

    def ask(self, prompt):
        """Generate a response while keeping Atlas alive when Ollama fails."""
        if not isinstance(prompt, str) or not prompt.strip():
            return "I need a message to think about."

        attempts = self.retries + 1
        for attempt in range(attempts):
            try:
                return self._request(prompt)
            except requests.ConnectionError as exc:
                if attempt + 1 < attempts:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                return (
                    "I can't reach Ollama right now. Atlas is still running, "
                    "but my local language model is unavailable."
                )
            except requests.Timeout:
                if attempt + 1 < attempts:
                    continue
                return "The local model took too long to respond. Please try again."
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status == 404:
                    return (
                        f"The Ollama model '{self.model}' is not available. "
                        f"Please make sure that model is installed locally."
                    )
                return f"Ollama returned an HTTP error ({status or 'unknown'})."
            except OllamaError as exc:
                return f"Local model error: {exc}"
            except requests.RequestException as exc:
                return f"Local model connection error: {exc}"

        return "The local model is temporarily unavailable."
