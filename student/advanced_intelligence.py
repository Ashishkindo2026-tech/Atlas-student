"""Phases 7-12: predictive, personalized and continuity intelligence.

Pure-stdlib, evidence-first services. They make predictions and recommendations,
not diagnoses; every prediction carries evidence and confidence.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Prediction:
    kind: str
    subject: str
    topic: str
    confidence: float
    reason: str
    action: str
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PredictiveIntelligence:
    """Turns existing evidence into conservative, explainable predictions."""

    def _groups(self, attempts: Iterable[Mapping[str, Any]]) -> Dict[tuple[str, str], List[Mapping[str, Any]]]:
        groups: Dict[tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
        for item in attempts:
            groups[(str(item.get("subject", "")), str(item.get("topic", "")))].append(item)
        return groups

    def predict_weak_chapters(self, attempts: Iterable[Mapping[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        for (subject, topic), rows in self._groups(attempts).items():
            if not rows:
                continue
            recent = rows[-8:]
            errors = sum(not bool(x.get("correct")) for x in recent)
            rate = errors / len(recent)
            if len(recent) >= 2 and rate >= 0.35:
                results.append(Prediction("weak_topic", subject, topic, min(0.99, round(0.55 + rate * .4, 2)), f"{errors}/{len(recent)} recent attempts were incorrect", "Review concept, then do targeted practice").to_dict())
        return sorted(results, key=lambda x: x["confidence"], reverse=True)[:limit]

    def detect_falling_performance(self, attempts: Iterable[Mapping[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        for (subject, topic), rows in self._groups(attempts).items():
            if len(rows) < 4:
                continue
            scores = [1.0 if bool(x.get("correct")) else 0.0 for x in rows]
            half = len(scores) // 2
            earlier, recent = mean(scores[:half]), mean(scores[half:])
            drop = earlier - recent
            if drop >= 0.20:
                results.append(Prediction("falling_performance", subject, topic, min(0.95, round(.55 + drop, 2)), f"Accuracy fell from {earlier:.0%} to {recent:.0%}", "Schedule a short diagnostic and revision block").to_dict())
        return sorted(results, key=lambda x: x["confidence"], reverse=True)[:limit]

    def revision_due(self, topics: Iterable[Mapping[str, Any]], now: Optional[datetime] = None, limit: int = 5) -> List[Dict[str, Any]]:
        now = now or datetime.now(timezone.utc)
        results = []
        for item in topics:
            last = item.get("last_reviewed")
            if not last:
                continue
            try:
                dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
            except ValueError:
                continue
            days = max(0, (now - dt).days)
            mastery = float(item.get("mastery", 0))
            interval = max(1, round(2 + mastery / 20))
            if days >= interval:
                results.append(Prediction("revision_due", str(item.get("subject", "")), str(item.get("topic", "")), min(.99, .5 + days / max(1, interval * 10)), f"Last reviewed {days} days ago; estimated interval is {interval} days", "Revise before new material").to_dict())
        return sorted(results, key=lambda x: x["confidence"], reverse=True)[:limit]

    def recommend_next(self, weak: Iterable[Mapping[str, Any]], due: Iterable[Mapping[str, Any]], goals: Iterable[Mapping[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for item in due:
            candidates.append({"priority": 3, "action": "revise", "subject": item.get("subject"), "topic": item.get("topic"), "reason": item.get("reason")})
        for item in weak:
            candidates.append({"priority": 2, "action": "targeted_practice", "subject": item.get("subject"), "topic": item.get("topic"), "reason": item.get("reason")})
        for goal in goals:
            if not goal.get("done"):
                candidates.append({"priority": 1, "action": "goal_step", "subject": goal.get("subject", ""), "topic": goal.get("goal", ""), "reason": "Active student goal"})
        return sorted(candidates, key=lambda x: x["priority"], reverse=True)[:limit]


class LearningCoach:
    """Adapts teaching from observed outcomes instead of fixed personality guesses."""

    STYLES = ("worked_example", "step_by_step", "visual", "analogy", "practice_first")

    def best_style(self, outcomes: Iterable[Mapping[str, Any]]) -> str:
        scores: Dict[str, List[float]] = defaultdict(list)
        for row in outcomes:
            style = str(row.get("style", ""))
            if style in self.STYLES and "score" in row:
                scores[style].append(float(row["score"]))
        if not scores:
            return "step_by_step"
        return max(scores, key=lambda s: mean(scores[s]))

    def teaching_plan(self, mastery: float, preferred_style: str, difficulty: int = 1) -> Dict[str, Any]:
        mastery = max(0.0, min(100.0, float(mastery)))
        if mastery < 40:
            level, action = "foundation", "explain prerequisites and use a worked example"
        elif mastery < 75:
            level, action = "guided", "explain briefly, then practice with hints"
        else:
            level, action = "challenge", "use mixed application problems and retrieval practice"
        return {"level": level, "style": preferred_style if preferred_style in self.STYLES else "step_by_step", "difficulty": max(1, min(5, int(difficulty))), "action": action}

    def missing_prerequisites(self, concept: str, prerequisite_map: Mapping[str, Iterable[str]], mastered: Iterable[str]) -> List[str]:
        known = {str(x).casefold() for x in mastered}
        return [p for p in prerequisite_map.get(concept, ()) if str(p).casefold() not in known]


class AutonomousStudyPlanner:
    """Builds a complete study session: plan -> teach -> practice -> test -> analyze -> revise."""

    STEPS = ("plan", "teach", "practice", "test", "analyze", "revise")

    def session(self, minutes: int, focus: str, recommendations: Iterable[Mapping[str, Any]] = ()) -> Dict[str, Any]:
        minutes = max(10, int(minutes))
        weights = {"plan": .08, "teach": .25, "practice": .25, "test": .17, "analyze": .10, "revise": .15}
        blocks = []
        remaining = minutes
        for i, step in enumerate(self.STEPS):
            block = max(1, round(minutes * weights[step])) if i < len(self.STEPS) - 1 else remaining
            remaining -= block
            blocks.append({"step": step, "minutes": block, "focus": focus})
        return {"minutes": minutes, "focus": focus, "blocks": blocks, "recommendations": list(recommendations)}


class RealWorldAssistant:
    """Local planning layer for school, tuition, assignments, deadlines and projects."""

    def prioritize(self, tasks: Iterable[Mapping[str, Any]], now: Optional[datetime] = None, limit: int = 10) -> List[Dict[str, Any]]:
        now = now or datetime.now(timezone.utc)
        output = []
        for task in tasks:
            due = task.get("due")
            urgency = 0
            if due:
                try:
                    dt = datetime.fromisoformat(str(due).replace("Z", "+00:00")); hours = (dt - now).total_seconds() / 3600
                    urgency = 3 if hours <= 24 else 2 if hours <= 72 else 1
                except ValueError:
                    urgency = 0
            output.append({**dict(task), "urgency": urgency, "priority": urgency + int(task.get("importance", 0))})
        return sorted(output, key=lambda x: x["priority"], reverse=True)[:limit]


class StudentDigitalTwin:
    """A compact evidence model of the student's academic journey."""

    def build(self, attempts: Iterable[Mapping[str, Any]], mistakes: Iterable[Mapping[str, Any]], goals: Iterable[Mapping[str, Any]], interests: Iterable[str] = ()) -> Dict[str, Any]:
        attempts = list(attempts); mistakes = list(mistakes); goals = list(goals)
        accuracy = mean([1 if x.get("correct") else 0 for x in attempts]) * 100 if attempts else 0.0
        return {
            "generated_at": _now(),
            "knowledge": {"attempts": len(attempts), "accuracy": round(accuracy, 1)},
            "skills": sorted({str(x.get("topic")) for x in attempts if x.get("topic")}),
            "mistakes": len(mistakes),
            "goals": [dict(x) for x in goals],
            "interests": sorted({str(x) for x in interests if str(x).strip()}),
        }

    def monthly_focus(self, twin: Mapping[str, Any], weak_topics: Iterable[Mapping[str, Any]], goals: Iterable[Mapping[str, Any]]) -> List[str]:
        focus = [f"Strengthen {x.get('topic')}" for x in list(weak_topics)[:3]]
        focus.extend(f"Progress: {x.get('goal')}" for x in goals if not x.get("done"))
        return focus[:5] or ["Run a baseline assessment"]


class AtlasContinuity:
    """Export/import contract for Atlas Student -> full Atlas continuity."""

    VERSION = 1

    def export(self, memory: Mapping[str, Any], achievements: Iterable[Mapping[str, Any]], projects: Iterable[Mapping[str, Any]], learning_history: Iterable[Mapping[str, Any]], preferences: Mapping[str, Any]) -> Dict[str, Any]:
        return {"schema": "atlas.student.continuity", "version": self.VERSION, "exported_at": _now(), "knowledge": dict(memory), "achievements": list(achievements), "projects": list(projects), "learning_history": list(learning_history), "preferences": dict(preferences)}

    def validate(self, bundle: Mapping[str, Any]) -> bool:
        required = {"schema", "version", "knowledge", "achievements", "projects", "learning_history", "preferences"}
        return bundle.get("schema") == "atlas.student.continuity" and int(bundle.get("version", -1)) == self.VERSION and required.issubset(bundle)

    def migrate(self, bundle: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.validate(bundle):
            raise ValueError("invalid Atlas continuity bundle")
        return dict(bundle)


class AdvancedStudentSystem:
    """Single facade for Phases 7-12."""
    def __init__(self) -> None:
        self.predictive = PredictiveIntelligence()
        self.coach = LearningCoach()
        self.autonomous = AutonomousStudyPlanner()
        self.real_world = RealWorldAssistant()
        self.digital_twin = StudentDigitalTwin()
        self.continuity = AtlasContinuity()

    def analyze(self, attempts, topics=(), goals=()):
        weak = self.predictive.predict_weak_chapters(attempts)
        falling = self.predictive.detect_falling_performance(attempts)
        due = self.predictive.revision_due(topics)
        return {"weak_predictions": weak, "falling_performance": falling, "revision_due": due, "next": self.predictive.recommend_next(weak, due, goals)}
