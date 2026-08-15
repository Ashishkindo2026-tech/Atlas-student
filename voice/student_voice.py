"""Voice interface for Atlas Student.

Keeps speech I/O separate from the brain so text and voice share one agent.
"""
from __future__ import annotations

from typing import Callable, Optional

HINGLISH_MARKERS = {
    "kya", "kaise", "kaun", "mera", "meri", "tum", "aaj", "kal", "hai",
    "ho", "kyu", "kyon", "kab", "kitna", "acha", "accha", "bura", "mujhe",
    "chahiye", "karna", "karo", "batao", "padhai"
}


def detect_hinglish(text: str) -> bool:
    words = {word.strip(".,!?;:").lower() for word in text.split()}
    return len(words & HINGLISH_MARKERS) >= 1


class StudentVoice:
    def __init__(self, processor: Callable[[str], str], speaker: Optional[Callable[[str], None]] = None):
        self.processor = processor
        self.speaker = speaker

    def handle_text(self, text: str) -> str:
        response = str(self.processor(text))
        if self.speaker:
            self.speaker(response)
        return response

    def run_once(self, listener: Callable[[], str]) -> str:
        text = listener()
        if not text or text.lower().startswith("error"):
            return ""
        return self.handle_text(text)
