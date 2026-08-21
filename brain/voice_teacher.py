"""Voice-teaching adapter for Atlas Student.

This module keeps teaching logic independent from the concrete speech engine.
A caller can supply a speaker function, while text-only use remains fully
supported for laptops without audio dependencies.
"""
from __future__ import annotations

from typing import Callable, Optional


class VoiceTeacher:
    """Turn a teaching response into optional spoken output."""

    def __init__(self, speaker: Optional[Callable[[str], None]] = None) -> None:
        self.speaker = speaker

    def teach(self, text: str) -> str:
        """Return *text* and speak it when a speaker callback is configured."""
        lesson = str(text).strip()
        if not lesson:
            return ""
        if self.speaker is not None:
            self.speaker(lesson)
        return lesson

    def available(self) -> bool:
        """Whether this instance has an active speech output callback."""
        return self.speaker is not None
