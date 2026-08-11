"""Deterministic study-planning layer for Atlas Student.

The planner does not invent chapters. It works from retrieved NCERT chunks and
explicitly recorded progress, then allocates only the time the student supplied.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StudyBlock:
    minutes: int
    title: str
    reason: str


def _mastery_for(progress: Dict, subject: str, concept: str) -> int | None:
    key = f"{subject}::{concept}"
    item = progress.get("concepts", {}).get(key)
    if isinstance(item, dict) and isinstance(item.get("mastery"), int):
        return item["mastery"]
    return None


def build_study_plan(subject: str, minutes: int, retrieved: List[Dict], progress: Dict) -> List[StudyBlock]:
    if not subject.strip() or minutes <= 0:
        return []
    if not retrieved:
        return []

    candidates = []
    seen = set()
    for item in retrieved:
        chapter = (item.get("chapter") or "").strip()
        section = (item.get("section") or "").strip()
        title = section or chapter or "NCERT material"
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        mastery = _mastery_for(progress, subject, section or chapter) if section or chapter else None
        score = float(item.get("score", 0.0) or 0.0)
        priority = (100 - mastery) if mastery is not None else 50
        candidates.append((priority + score * 10, title, mastery))

    candidates.sort(reverse=True)
    count = min(len(candidates), max(1, minutes // 20))
    selected = candidates[:count]
    blocks: List[StudyBlock] = []

    # Reserve a final recall block when enough time exists.
    study_minutes = minutes - 10 if minutes >= 30 else minutes
    base = max(10, study_minutes // len(selected))
    remainder = study_minutes - base * len(selected)
    for i, (_, title, mastery) in enumerate(selected):
        allocated = base + (remainder if i == len(selected) - 1 else 0)
        reason = "review recorded weak area" if mastery is not None and mastery < 60 else "review retrieved NCERT material"
        blocks.append(StudyBlock(allocated, title, reason))
    if minutes >= 30:
        blocks.append(StudyBlock(10, "Active recall + quick self-test", "verify what you can reproduce without notes"))
    return blocks


def format_plan(subject: str, minutes: int, blocks: List[StudyBlock]) -> str:
    if not blocks:
        return f"I need indexed NCERT material for {subject} before I can build a source-grounded plan."
    lines = [f"{subject} — {minutes}-minute NCERT revision plan:"]
    total = 0
    for i, block in enumerate(blocks, 1):
        lines.append(f"{i}. {block.minutes} min — {block.title} ({block.reason})")
        total += block.minutes
    lines.append(f"Total: {total} minutes")
    return "\n".join(lines)
