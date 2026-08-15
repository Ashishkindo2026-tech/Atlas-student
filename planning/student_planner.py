"""Deterministic study planning for Atlas Student."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StudyBlock:
    minutes: int
    task: str
    source: str = ""


class StudentPlanner:
    def build(self, subject: str, minutes: int, retrieved: List[Dict] | None = None, progress: Dict | None = None) -> List[StudyBlock]:
        subject = subject.strip().title()
        minutes = max(1, int(minutes))
        retrieved = retrieved or []
        progress = progress or {}

        weak = []
        for item in progress.get("mastery", []):
            if str(item.get("subject", "")).lower() == subject.lower() and int(item.get("score", 0)) < 60:
                weak.append(str(item.get("concept", "")))
        source = str(retrieved[0].get("source", "local curriculum")) if retrieved else "student knowledge / local curriculum"

        if minutes <= 15:
            blocks = [(minutes, "Rapid recall + 3 self-test questions")]
        elif minutes <= 45:
            a = max(10, int(minutes * 0.30)); b = max(10, int(minutes * 0.40)); c = max(5, minutes - a - b)
            blocks = [(a, "Recall key ideas"), (b, "Solve representative questions"), (c, "Closed-book self-test + correction")]
        else:
            a = max(15, int(minutes * 0.25)); b = max(20, int(minutes * 0.40)); c = max(10, int(minutes * 0.25)); d = max(5, minutes - a - b - c)
            blocks = [(a, "Concept review"), (b, "Guided practice"), (c, "Mixed problems"), (d, "Active recall + error log")]

        if weak:
            blocks[0] = (blocks[0][0], "Target weak concept: " + ", ".join(weak[:2]))
        return [StudyBlock(m, task, source) for m, task in blocks]

    @staticmethod
    def format(subject: str, minutes: int, blocks: List[StudyBlock]) -> str:
        lines = [f"Atlas Student plan — {subject} ({minutes} min)", ""]
        elapsed = 0
        for index, block in enumerate(blocks, 1):
            elapsed += block.minutes
            lines.append(f"{index}. {block.minutes} min — {block.task}")
        lines += ["", f"Total: {elapsed} min", f"Source: {blocks[0].source if blocks else 'local'}"]
        return "\n".join(lines)
