"""Deterministic multi-subject exam planning for explicit chapter-count requests."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExamSubject:
    name: str
    chapters: int


def build_month_plan(days: int, subjects: list[ExamSubject]) -> str:
    if days <= 0 or not subjects:
        return "I need the exam duration and chapter counts to build the plan."

    total_chapters = sum(s.chapters for s in subjects)
    revision_days = max(3, round(days * 0.2))
    learning_days = max(1, days - revision_days)
    lines = [
        f"📚 {days}-day half-yearly preparation plan",
        f"Total chapters: {total_chapters}",
        "",
        "Subject load:",
    ]
    for s in subjects:
        share = (s.chapters / total_chapters) * 100 if total_chapters else 0
        lines.append(f"• {s.name.title()}: {s.chapters} chapters ({share:.0f}% of chapter load)")

    lines += [
        "",
        f"Days 1–{learning_days}: finish the new chapters.",
        f"Days {learning_days + 1}–{days}: revision, mixed practice and mock tests.",
        "",
        "Recommended rotation:",
    ]
    for subject in subjects:
        focused = max(1, round(learning_days * subject.chapters / total_chapters))
        lines.append(f"• {subject.name.title()}: about {focused} focused study days")

    lines += [
        "",
        "Daily pattern:",
        "1. Learn/revise one chapter section",
        "2. Solve questions without looking at the solution",
        "3. Mark mistakes and weak concepts",
        "4. Spend 10–15 minutes recalling previous work",
        "",
        "Final revision: weakest chapters → formulas/reactions/key results → mixed questions → timed mocks + error review.",
        "",
        "I did not invent chapter names. Give Atlas the actual chapter names (or indexed NCERT material) for a chapter-by-chapter calendar.",
    ]
    return "\n".join(lines)
