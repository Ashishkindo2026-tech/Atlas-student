"""Stable multimodal input contracts for Atlas Student.

The brain receives normalized inputs instead of depending on a specific GUI,
OCR, camera, or file implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputPacket:
    text: str = ""
    image_path: Path | None = None
    document_path: Path | None = None
    source: str = "unknown"

    def validate(self) -> None:
        if not any((self.text.strip(), self.image_path, self.document_path)):
            raise ValueError("InputPacket must contain text, image, or document input")
        for path in (self.image_path, self.document_path):
            if path is not None and not Path(path).is_file():
                raise FileNotFoundError(path)
