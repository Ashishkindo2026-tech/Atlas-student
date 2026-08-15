"""Deterministic reasoning layer for Atlas Student."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List


@dataclass(frozen=True)
class ReasoningPlan:
    intent: str
    steps: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    confidence: float = 0.0


class StudentReasoner:
    """Plans a response before the language model is called."""

    def analyze(self, text: str) -> ReasoningPlan:
        raw = text.strip()
        lower = raw.lower()
        if not raw:
            return ReasoningPlan("empty", ["ask for a task"], confidence=1.0)

        is_study = any(x in lower for x in ("study", "revise", "revision", "exam", "homework", "chapter", "learn"))
        is_plan = any(x in lower for x in ("plan", "schedule", "timetable", "how should i prepare"))
        is_memory = any(x in lower for x in ("remember", "forget", "what do you remember"))
        is_progress = any(x in lower for x in ("progress", "mastery", "weak", "improved"))

        if is_memory:
            intent = "memory"
        elif is_plan and is_study:
            intent = "study_planning"
        elif is_study:
            intent = "study_help"
        elif is_progress:
            intent = "progress"
        else:
            intent = "general"

        steps = ["identify intent", "collect only available student context", "check constraints", "produce a direct answer"]
        missing: List[str] = []
        if intent == "study_planning":
            if not re.search(r"\b\d+(?:\.\d+)?\s*(?:minutes?|mins?|hours?|hrs?)\b", lower):
                missing.append("time")
            if not re.search(r"physics|chemistry|mathematics|math|biology|english|history|geography|science|computer science", lower):
                missing.append("subject")
            steps.insert(2, "use indexed curriculum material when available")
        return ReasoningPlan(intent, steps, missing, 0.85 if intent != "general" else 0.65)

    def prompt_context(self, text: str) -> str:
        plan = self.analyze(text)
        lines = [f"Intent: {plan.intent}", f"Confidence: {plan.confidence:.2f}", "Reasoning steps:"]
        lines.extend(f"- {step}" for step in plan.steps)
        if plan.missing:
            lines.append("Missing constraints: " + ", ".join(plan.missing))
        else:
            lines.append("Missing constraints: none detected")
        return "\n".join(lines)
