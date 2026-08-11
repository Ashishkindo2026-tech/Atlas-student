"""Detect explicit learning signals without inventing mastery."""
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class LearningSignal:
    kind: str
    concept: str | None
    confidence: float
    evidence: str

_POSITIVE = re.compile(r"\b(now i understand|i understand|i got it|finally understand|makes sense|i learned|i know how)\b", re.I)
_NEGATIVE = re.compile(r"\b(don't understand|dont understand|still confused|i'm confused|im confused|don't get|dont get|can't understand|cannot understand)\b", re.I)


def detect(text: str, concept: str | None = None) -> LearningSignal | None:
    if not text or not text.strip():
        return None
    if _NEGATIVE.search(text):
        return LearningSignal("difficulty", concept, 0.90, text.strip())
    if _POSITIVE.search(text):
        return LearningSignal("understood", concept, 0.90, text.strip())
    return None
