"""Phase 17: reasoning-first coaching."""
from dataclasses import dataclass

@dataclass
class ReasoningReview:
    correct: bool
    gaps: list[str]
    hints: list[str]
    retry_required: bool

class ReasoningLab:
    def review(self, student_reasoning: str, evaluator):
        result = evaluator(student_reasoning)
        gaps = list(result.get("gaps", []))
        correct = bool(result.get("correct", False))
        return ReasoningReview(correct, gaps, list(result.get("hints", [])), not correct)
