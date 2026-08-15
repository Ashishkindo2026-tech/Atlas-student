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
    @staticmethod
    def _allocate(total: int, ratios: List[float], minimums: List[int]) -> List[int]:
        total = max(len(ratios), int(total))
        raw = [total * ratio for ratio in ratios]
        values = [max(minimum, int(value)) for value, minimum in zip(raw, minimums)]
        while sum(values) > total:
            index = max(range(len(values)), key=lambda i: values[i] - minimums[i])
            if values[index] <= minimums[index]:
                break
            values[index] -= 1
        while sum(values) < total:
            index = max(range(len(values)), key=lambda i: ratios[i])
            values[index] += 1
        return values

    def build(self, subject: str, minutes: int, retrieved: List[Dict] | None = None, progress: Dict | None = None) -> List[StudyBlock]:
        subject = subject.strip().title()
        minutes = max(1, int(minutes))
        retrieved = retrieved or []
        progress = progress or {}

        weak = []
        concepts = progress.get("concepts", {})
        items = concepts.values() if isinstance(concepts, dict) else concepts
        for item in items:
            try:
                score = int(item.get("mastery", 0))
            except (TypeError, ValueError):
                score = 0
            if str(item.get("subject", "")).lower() == subject.lower() and score < 60:
                weak.append(str(item.get("concept", "")))
        source = str(retrieved[0].get("source", "local curriculum")) if retrieved else "student knowledge / local curriculum"

        if minutes <= 15:
            sizes = [minutes]
            tasks = ["Rapid recall + 3 self-test questions"]
        elif minutes <= 45:
            sizes = self._allocate(minutes, [0.30, 0.40, 0.30], [5, 5, 5])
            tasks = ["Recall key ideas", "Solve representative questions", "Closed-book self-test + correction"]
        else:
            sizes = self._allocate(minutes, [0.25, 0.40, 0.25, 0.10], [5, 5, 5, 5])
            tasks = ["Concept review", "Guided practice", "Mixed problems", "Active recall + error log"]

        if weak:
            tasks[0] = "Target weak concept: " + ", ".join(weak[:2])
        return [StudyBlock(m, task, source) for m, task in zip(sizes, tasks)]

    @staticmethod
    def format(subject: str, minutes: int, blocks: List[StudyBlock]) -> str:
        lines = [f"Atlas Student plan — {subject} ({minutes} min)", ""]
        elapsed = 0
        for index, block in enumerate(blocks, 1):
            elapsed += block.minutes
            lines.append(f"{index}. {block.minutes} min — {block.task}")
        lines += ["", f"Total: {elapsed} min", f"Source: {blocks[0].source if blocks else 'local'}"]
        return "\n".join(lines)
