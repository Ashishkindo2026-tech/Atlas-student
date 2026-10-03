"""Evidence-driven learning, practice, mastery, and spaced revision.

This module is local-only and stdlib-only. It complements the existing
StudentIntelligence class with explicit topic state, attempts, revision history,
adaptive difficulty, and deterministic practice plans.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "learning_state.json"

DEFAULT = {
    "subjects": {},
    "topics": {},
    "attempts": [],
    "revisions": [],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds")


def _load() -> dict[str, Any]:
    try:
        raw = json.loads(FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            data = dict(DEFAULT)
            for key in DEFAULT:
                if isinstance(raw.get(key), type(DEFAULT[key])):
                    data[key] = raw[key]
            return data
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return {k: (v.copy() if isinstance(v, dict) else list(v)) for k, v in DEFAULT.items()}


def _save(data: dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FILE)


class LearningSystem:
    """Single local store for topic state and evidence."""

    def data(self) -> dict[str, Any]:
        return _load()

    def register_subject(self, subject: str) -> bool:
        subject = str(subject).strip()
        if not subject:
            return False
        data = _load()
        data["subjects"].setdefault(subject, {"topics": [], "minutes": 0, "sessions": 0})
        _save(data)
        return True

    def register_topic(self, subject: str, topic: str) -> bool:
        subject, topic = str(subject).strip(), str(topic).strip()
        if not subject or not topic:
            return False
        data = _load()
        subject_state = data["subjects"].setdefault(subject, {"topics": [], "minutes": 0, "sessions": 0})
        if topic not in subject_state["topics"]:
            subject_state["topics"].append(topic)
        key = f"{subject}::{topic}"
        data["topics"].setdefault(key, {
            "subject": subject, "topic": topic, "attempts": 0, "correct": 0,
            "mastery": 0.0, "weak": False, "strong": False, "last_reviewed": None,
            "next_review": None, "review_streak": 0,
        })
        _save(data)
        return True

    def record_session(self, subject: str, minutes: int, topic: str = "") -> dict[str, Any]:
        subject, minutes = str(subject).strip(), int(minutes)
        if not subject or minutes <= 0:
            raise ValueError("subject and positive minutes are required")
        data = _load()
        state = data["subjects"].setdefault(subject, {"topics": [], "minutes": 0, "sessions": 0})
        state["minutes"] += minutes
        state["sessions"] += 1
        if topic:
            self.register_topic(subject, topic)
        _save(data)
        return {"subject": subject, "minutes": minutes, "topic": topic.strip(), "at": _stamp()}

    def record_attempt(self, subject: str, topic: str, correct: bool, difficulty: int = 1) -> dict[str, Any]:
        subject, topic = str(subject).strip(), str(topic).strip()
        if not subject or not topic:
            raise ValueError("subject and topic are required")
        self.register_topic(subject, topic)
        data = _load()
        difficulty = max(1, min(5, int(difficulty)))
        item = {"subject": subject, "topic": topic, "correct": bool(correct),
                "difficulty": difficulty, "at": _stamp()}
        data["attempts"].append(item)
        data["attempts"] = data["attempts"][-1000:]
        state = data["topics"][f"{subject}::{topic}"]
        state["attempts"] += 1
        state["correct"] += int(bool(correct))
        state["mastery"] = round(100.0 * state["correct"] / max(1, state["attempts"]), 1)
        state["weak"] = state["mastery"] < 60 and state["attempts"] >= 2
        state["strong"] = state["mastery"] >= 85 and state["attempts"] >= 3
        _save(data)
        return item

    def topic(self, subject: str, topic: str) -> dict[str, Any]:
        self.register_topic(subject, topic)
        return _load()["topics"][f"{subject.strip()}::{topic.strip()}"]

    def weak_topics(self, subject: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        rows = [x for x in _load()["topics"].values() if x.get("weak")]
        if subject:
            rows = [x for x in rows if x.get("subject", "").casefold() == subject.casefold()]
        return sorted(rows, key=lambda x: (x.get("mastery", 0), x.get("attempts", 0)))[:limit]

    def strong_topics(self, subject: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        rows = [x for x in _load()["topics"].values() if x.get("strong")]
        if subject:
            rows = [x for x in rows if x.get("subject", "").casefold() == subject.casefold()]
        return sorted(rows, key=lambda x: x.get("mastery", 0), reverse=True)[:limit]

    def next_difficulty(self, subject: str, topic: str) -> int:
        state = self.topic(subject, topic)
        mastery = float(state.get("mastery", 0))
        if state.get("attempts", 0) == 0:
            return 1
        if mastery < 45:
            return 1
        if mastery < 70:
            return 2
        if mastery < 85:
            return 3
        if mastery < 95:
            return 4
        return 5

    def practice_plan(self, subject: str, topic: str, count: int = 5) -> list[dict[str, Any]]:
        count = max(1, min(50, int(count)))
        difficulty = self.next_difficulty(subject, topic)
        return [{"index": i + 1, "subject": subject, "topic": topic,
                 "difficulty": min(5, difficulty + ((i - 1) // 3)),
                 "type": "practice"} for i in range(count)]

    def schedule_revision(self, subject: str, topic: str, mastery: float | None = None,
                          reviewed_at: datetime | None = None) -> dict[str, Any]:
        self.register_topic(subject, topic)
        data = _load()
        state = data["topics"][f"{subject.strip()}::{topic.strip()}"]
        mastery = float(state.get("mastery", 0) if mastery is None else mastery)
        previous = int(state.get("review_streak", 0))
        if mastery < 50:
            interval_days = 1
        elif mastery < 70:
            interval_days = 2
        elif mastery < 85:
            interval_days = 4
        elif mastery < 95:
            interval_days = 7
        else:
            interval_days = 14
        if previous:
            interval_days = min(30, interval_days + min(previous, 5))
        reviewed = reviewed_at or _now()
        next_review = reviewed + timedelta(days=interval_days)
        state.update({
            "last_reviewed": _stamp(reviewed),
            "next_review": _stamp(next_review),
            "review_streak": previous + 1,
        })
        data["revisions"].append({
            "subject": subject.strip(), "topic": topic.strip(),
            "reviewed_at": _stamp(reviewed), "next_review": _stamp(next_review),
            "interval_days": interval_days, "mastery": mastery,
        })
        data["revisions"] = data["revisions"][-500:]
        _save(data)
        return data["revisions"][-1]

    def due_revisions(self, now: datetime | None = None, limit: int = 10) -> list[dict[str, Any]]:
        current = now or _now()
        due = []
        for state in _load()["topics"].values():
            raw = state.get("next_review")
            if not raw:
                continue
            try:
                next_review = datetime.fromisoformat(str(raw))
            except ValueError:
                continue
            if next_review <= current:
                due.append(dict(state))
        return sorted(due, key=lambda x: x.get("next_review") or "")[:limit]

    def next_path(self, subject: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        weak = self.weak_topics(subject, limit)
        if weak:
            return [{"step": "targeted_practice", "subject": x["subject"], "topic": x["topic"],
                     "difficulty": self.next_difficulty(x["subject"], x["topic"])} for x in weak]
        due = self.due_revisions(limit=limit)
        if due:
            return [{"step": "revision", "subject": x["subject"], "topic": x["topic"],
                     "difficulty": self.next_difficulty(x["subject"], x["topic"])} for x in due]
        return [{"step": "diagnostic", "subject": subject or "any", "topic": "baseline assessment"}]


def reset() -> None:
    _save({k: (v.copy() if isinstance(v, dict) else list(v)) for k, v in DEFAULT.items()})
