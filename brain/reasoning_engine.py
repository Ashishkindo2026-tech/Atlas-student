import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ReasoningPlan:
    intent: str
    constraints: Dict[str, str] = field(default_factory=dict)
    steps: List[str] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)


class ReasoningEngine:
    """Deterministic planning layer that separates known facts from missing constraints."""

    def understand(self, text: str) -> Dict[str, str]:
        lower = text.lower()
        intent = "general"
        if any(w in lower for w in ("exam", "test", "revision", "study")):
            intent = "study_planning"
        elif any(w in lower for w in ("plan", "schedule", "finish", "deadline")):
            intent = "planning"
        elif any(w in lower for w in ("decide", "should i", "which", "choose")):
            intent = "decision"

        constraints = {}
        hour_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b", lower)
        if hour_match:
            constraints["available_hours"] = hour_match.group(1)
        min_match = re.search(r"\b(\d+)\s*(?:minutes?|mins?)\b", lower)
        if min_match:
            constraints["available_minutes"] = min_match.group(1)
        if "tomorrow" in lower:
            constraints["deadline"] = "tomorrow"
        return {"intent": intent, **constraints}

    def plan(self, text: str, context=None) -> ReasoningPlan:
        understood = self.understand(text)
        intent = understood.pop("intent")
        missing = []

        # A study plan is not safe to specialize until the subject is actually known.
        if intent == "study_planning":
            if not self._subject_is_explicit(text):
                missing.append("subject")
            steps = [
                "Identify the subject and highest-priority material.",
                "Use available time for active recall and targeted practice.",
                "Leave a short final review and buffer.",
            ]
            verification = [
                "Check that total study time fits the stated limit.",
                "Check that a realistic break/buffer remains.",
                "Do not invent a subject, syllabus, or topics that the user did not provide.",
            ]
        elif intent == "planning":
            steps = [
                "Identify the desired outcome.",
                "Break it into the smallest useful actions.",
                "Order actions by priority and deadline.",
            ]
            verification = ["Check for conflicting constraints and unrealistic timing."]
        elif intent == "decision":
            steps = [
                "Identify the decision and constraints.",
                "Compare relevant options against those constraints.",
                "State trade-offs and recommendation.",
            ]
            verification = ["Check that the recommendation follows from the stated constraints."]
        else:
            steps, verification = [], []

        return ReasoningPlan(intent, understood, steps, verification, missing)

    @staticmethod
    def _subject_is_explicit(text: str) -> bool:
        lower = text.lower()
        patterns = (
            r"\b(?:for|in|of)\s+(?:my\s+)?(?:math|maths|mathematics|physics|chemistry|biology|english|history|geography|computer science|cs|science)\b",
            r"\b(?:physics|chemistry|biology|math|maths|mathematics|english|history|geography|computer science|cs|science)\s+(?:exam|test|paper)\b",
            r"\b(?:exam|test|paper)\s+(?:is|for)\s+(?:math|maths|mathematics|physics|chemistry|biology|english|history|geography|computer science|cs|science)\b",
        )
        return any(re.search(pattern, lower) for pattern in patterns)

    def prompt_context(self, text: str, context=None) -> str:
        plan = self.plan(text, context)
        lines = [f"REASONING INTENT: {plan.intent}"]
        if plan.constraints:
            lines.append("KNOWN CONSTRAINTS: " + ", ".join(f"{k}={v}" for k, v in plan.constraints.items()))
        if plan.missing:
            lines.append("MISSING REQUIRED INFORMATION: " + ", ".join(plan.missing))
        if plan.steps:
            lines.append("PLANNING STEPS:\n" + "\n".join(f"- {s}" for s in plan.steps))
        if plan.verification:
            lines.append("VERIFICATION CHECKS:\n" + "\n".join(f"- {s}" for s in plan.verification))
        lines.append("RULE: Never turn a preference or unrelated memory into a current fact. Never invent missing constraints.")
        return "\n".join(lines)
