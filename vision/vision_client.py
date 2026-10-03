"""Local Ollama vision adapter for Atlas Student.

Vision is optional: Atlas can use any locally installed Ollama multimodal model.
The text-only student model remains untouched when no image is supplied.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Optional

import requests


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_IMAGE_BYTES = 12 * 1024 * 1024


class VisionClient:
    def __init__(self, model: str = "qwen2.5vl:3b", endpoint: str = "http://localhost:11434/api/chat"):
        self.model = model
        self.endpoint = endpoint

    @staticmethod
    def validate_image(path: str) -> Path:
        file = Path(path).expanduser().resolve()
        if not file.is_file():
            raise FileNotFoundError(str(file))
        if file.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported image type: {file.suffix or 'none'}")
        if file.stat().st_size <= 0:
            raise ValueError("Image file is empty or unreadable.")
        if file.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image is larger than the 12 MB local safety limit.")
        mime, _ = mimetypes.guess_type(file.name)
        if not mime or not mime.startswith("image/"):
            raise ValueError("The selected file is not recognized as an image.")
        try:
            from PIL import Image
            with Image.open(file) as image:
                image.verify()
        except ImportError:
            # Pillow is optional; extension/mime/size validation still protects the
            # local boundary when Pillow is not installed.
            pass
        except Exception as exc:
            raise ValueError(f"Image could not be read: {exc}") from exc
        return file

    @classmethod
    def encode_image(cls, path: str) -> str:
        file = cls.validate_image(path)
        return base64.b64encode(file.read_bytes()).decode("ascii")

    def describe(self, path: str, prompt: str = "Explain what is relevant in this image for a student.") -> str:
        encoded = self.encode_image(path)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt, "images": [encoded]}],
            "stream": False,
        }
        response = requests.post(self.endpoint, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return str(data.get("message", {}).get("content", "No vision response."))

    def available(self) -> bool:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if not response.ok:
                return False
            models = {m.get("name", "") for m in response.json().get("models", [])}
            return self.model in models
        except Exception:
            return False
