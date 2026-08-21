"""Offline wake-word gate for Atlas voice input.

This lightweight gate is intentionally model-agnostic. A future acoustic
wake-word engine can call `accept()` with recognized speech without changing
the rest of Atlas.
"""
from __future__ import annotations

import re


class WakeWord:
    def __init__(self, phrase: str = "hey atlas") -> None:
        phrase = phrase.strip().lower()
        if not phrase:
            raise ValueError("wake phrase cannot be empty")
        self.phrase = phrase
        self._pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)

    def accept(self, text: str) -> tuple[bool, str]:
        if not isinstance(text, str):
            return False, ""
        match = self._pattern.search(text)
        if not match:
            return False, ""
        remainder = (text[:match.start()] + text[match.end():]).strip(" ,.!?")
        return True, remainder
