import re
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ReasoningPlan:
    intent: str
    constraints: Dict[str, str] = field(default_factory=dict)
    steps: List[str] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)

class ReasoningEngine:
    """Lightweight deterministic planning layer before the local LLM."""
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
        if hour_match: constraints["available_hours"] = hour_match.group(1)
        min_match = re.search(r"\b(\d+)\s*(?:minutes?|mins?)\b", lower)
        if min_match: constraints["available_minutes"] = min_match.group(1)
        if "tomorrow" in lower: constraints["deadline"] = "tomorrow"
        return {"intent": intent, **constraints}
    def plan(self, text: str, context=None) -> ReasoningPlan:
        understood = self.understand(text)
        intent = understood.pop("intent")
        if intent == "study_planning":
            steps = ["Identify the subject and highest-priority material.", "Use available time for active recall and targeted practice.", "Leave a short final review and buffer."]
            verification = ["Check that total study time fits the stated limit.", "Check that a realistic break/buffer remains."]
        elif intent == "planning":
            steps = ["Identify the desired outcome.", "Break it into the smallest useful actions.", "Order actions by priority and deadline."]
            verification = ["Check for conflicting constraints and unrealistic timing."]
        elif intent == "decision":
            steps = ["Identify the decision and constraints.", "Compare relevant options against those constraints.", "State trade-offs and recommendation."]
            verification = ["Check that the recommendation follows from the stated constraints."]
        else:
            steps, verification = [], []
        return ReasoningPlan(intent, understood, steps, verification)
    def prompt_context(self, text: str, context=None) -> str:
        p = self.plan(text, context)
        lines = [f"REASONING INTENT: {p.intent}"]
        if p.constraints: lines.append("CONSTRAINTS: " + ", ".join(f"{k}={v}" for k,v in p.constraints.items()))
        if p.steps: lines.append("PLANNING STEPS:\n" + "\n".join(f"- {s}" for s in p.steps))
        if p.verification: lines.append("VERIFICATION CHECKS:\n" + "\n".join(f"- {s}" for s in p.verification))
        lines.append("Use this as a planning scaffold; do not invent missing facts.")
        return "\n".join(lines)
