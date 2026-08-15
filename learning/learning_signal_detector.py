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
_NEGATIVE = re.compile(r"\b(don't understand|dont understand|still confused|i'm confused|im confused|don't get|dont get|can't understand|cannot understand|made mistakes?|made an? mistake|keep making mistakes?|getting mistakes?|struggling with|weak in|weak at|bad at)\b", re.I)
_CONCEPT = re.compile(
    r"\b(?:understand|understood|confused about|don't understand|dont understand|don't get|dont get|mistakes? in|mistake in|struggling with|weak in|weak at|bad at)\s+(?:the\s+)?(.+?)(?:[.!?]|$)",
    re.I,
)


def _clean_concept(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" \t\n.,!?;:")
    if not value or len(value) > 120:
        return None
    return value


def detect(text: str, concept: str | None = None) -> LearningSignal | None:
    if not text or not text.strip():
        return None
    detected_concept = _clean_concept(concept)
    if detected_concept is None:
        match = _CONCEPT.search(text)
        detected_concept = _clean_concept(match.group(1) if match else None)
    if _NEGATIVE.search(text):
        return LearningSignal("difficulty", detected_concept, 0.90, text.strip())
    if _POSITIVE.search(text):
        return LearningSignal("understood", detected_concept, 0.90, text.strip())
    return None
