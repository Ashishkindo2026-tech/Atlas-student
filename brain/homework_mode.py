"""Homework-mode helpers: guide students without silently doing the work for them."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HomeworkMode:
    """Small deterministic state object used by student workflows."""

    subject: str = "general"
    step: int = 1

    def next_step(self) -> "HomeworkMode":
        if self.step < 1:
            raise ValueError("step must be >= 1")
        return HomeworkMode(subject=self.subject.strip() or "general", step=self.step + 1)

    def instruction(self, question: str) -> str:
        """Return a scaffold prompt for one homework question."""
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")
        return (
            f"Homework mode ({self.subject}, step {self.step}): "
            "f"break this question into one small reasoning step: {question}"
        )
