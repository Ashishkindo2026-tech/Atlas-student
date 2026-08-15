"""Student intelligence and adaptive-learning engine for Atlas Student."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "student" / "intelligence.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default() -> Dict[str, Any]:
    return {"mistakes": [], "goals": [], "profile": {}, "attempts": [], "weak_topics": []}


def _load() -> Dict[str, Any]:
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            base = _default(); base.update(data); return base
    except (OSError, json.JSONDecodeError):
        pass
    return _default()


def _save(data: Dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FILE)


class StudentIntelligence:
    """Evidence-based student model; it never treats a guess as a diagnosis."""

    def record_attempt(self, subject: str, topic: str, correct: bool, difficulty: int = 1) -> Dict[str, Any]:
        data = _load(); subject = subject.strip(); topic = topic.strip()
        if not subject or not topic: raise ValueError("subject and topic are required")
        item = {"subject": subject, "topic": topic, "correct": bool(correct),
                "difficulty": max(1, min(5, int(difficulty))), "at": _now()}
        data["attempts"].append(item); data["attempts"] = data["attempts"][-500:]
        self._recompute(data); _save(data); return item

    def record_mistake(self, subject: str, topic: str, error: str, correction: str = "") -> Dict[str, Any]:
        data = _load(); item = {"subject": subject.strip(), "topic": topic.strip(),
                "error": error.strip(), "correction": correction.strip(), "at": _now()}
        if not item["subject"] or not item["topic"] or not item["error"]: raise ValueError("subject, topic and error are required")
        data["mistakes"].append(item); data["mistakes"] = data["mistakes"][-300:]
        self._recompute(data); _save(data); return item

    def set_goal(self, goal: str, deadline: str = "", target: str = "") -> Dict[str, Any]:
        data = _load(); item = {"id": len(data["goals"]) + 1, "goal": goal.strip(), "deadline": deadline.strip(), "target": target.strip(), "done": False, "created_at": _now()}
        if not item["goal"]: raise ValueError("goal is required")
        data["goals"].append(item); _save(data); return item

    def complete_goal(self, goal_id: int) -> bool:
        data = _load()
        for item in data["goals"]:
            if item.get("id") == int(goal_id): item["done"] = True; _save(data); return True
        return False

    def set_profile(self, **fields: Any) -> Dict[str, Any]:
        data = _load(); data["profile"].update({k: v for k, v in fields.items() if v is not None}); _save(data); return data["profile"]

    def _recompute(self, data: Dict[str, Any]) -> None:
        stats: Dict[str, Dict[str, int]] = {}
        for a in data["attempts"]:
            key = f"{a['subject']}::{a['topic']}"; s = stats.setdefault(key, {"attempts": 0, "wrong": 0})
            s["attempts"] += 1; s["wrong"] += not a["correct"]
        for m in data["mistakes"]:
            key = f"{m['subject']}::{m['topic']}"; s = stats.setdefault(key, {"attempts": 0, "wrong": 0}); s["wrong"] += 1
        weak = []
        for key, s in stats.items():
            if s["wrong"] and (s["attempts"] == 0 or s["wrong"] / max(1, s["attempts"]) >= 0.30):
                subject, topic = key.split("::", 1); weak.append({"subject": subject, "topic": topic, "error_rate": round(s["wrong"] / max(1, s["attempts"]), 3), "evidence": s["wrong"]})
        data["weak_topics"] = sorted(weak, key=lambda x: x["error_rate"], reverse=True)

    def weak_topics(self, limit: int = 10) -> List[Dict[str, Any]]: return _load()["weak_topics"][:limit]
    def profile(self) -> Dict[str, Any]: return _load()["profile"]
    def data(self) -> Dict[str, Any]: return _load()


class AdaptiveLearning:
    """Turns evidence into a conservative next-step learning sequence."""
    def __init__(self, intelligence: StudentIntelligence | None = None): self.intelligence = intelligence or StudentIntelligence()

    def next_path(self, subject: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        weak = self.intelligence.weak_topics(50)
        if subject: weak = [x for x in weak if x["subject"].casefold() == subject.casefold()]
        return [{"step": "review", "subject": x["subject"], "topic": x["topic"]} for x in weak[:limit]] or [{"step": "diagnostic", "subject": subject or "any", "topic": "baseline assessment"}]

    def generate_questions(self, subject: str, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        # Question generation is deliberately model-agnostic: the LLM can turn these
        # blueprints into actual questions without coupling the data layer to a model.
        return [{"subject": subject, "topic": topic, "difficulty": min(5, 1 + i // 2), "type": "practice"} for i in range(max(1, int(count)))]

    def mastery(self, subject: str, topic: str) -> float:
        attempts = [a for a in _load()["attempts"] if a["subject"].casefold() == subject.casefold() and a["topic"].casefold() == topic.casefold()]
        return round(100 * sum(1 for a in attempts if a["correct"]) / len(attempts), 1) if attempts else 0.0
