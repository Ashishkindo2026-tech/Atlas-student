"""Long-term student growth: goals, habits, skills, history, and insights."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FILE = ROOT / "growth_state.json"
DEFAULT = {"goals": [], "habits": [], "skills": {}, "history": []}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict[str, Any]:
    try:
        raw = json.loads(FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {
                "goals": list(raw.get("goals", [])),
                "habits": list(raw.get("habits", [])),
                "skills": dict(raw.get("skills", {})),
                "history": list(raw.get("history", [])),
            }
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return {"goals": [], "habits": [], "skills": {}, "history": []}


def _save(data: dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FILE)


class GrowthSystem:
    def data(self) -> dict[str, Any]:
        return _load()

    def create_goal(self, text: str, deadline: str = "", target: str = "") -> dict[str, Any]:
        text = str(text).strip()
        if not text:
            raise ValueError("goal text is required")
        data = _load()
        item = {"id": self._next_id(data["goals"]), "text": text, "deadline": deadline.strip(),
                "target": target.strip(), "progress": 0, "done": False, "created_at": _now()}
        data["goals"].append(item)
        _save(data)
        return item

    def update_goal(self, goal_id: int, progress: int | None = None, done: bool | None = None) -> bool:
        data = _load()
        for item in data["goals"]:
            if int(item.get("id", -1)) == int(goal_id):
                if progress is not None:
                    item["progress"] = max(0, min(100, int(progress)))
                if done is not None:
                    item["done"] = bool(done)
                    if done:
                        item["progress"] = 100
                item["updated_at"] = _now()
                _save(data)
                return True
        return False

    def delete_goal(self, goal_id: int) -> bool:
        data = _load()
        before = len(data["goals"])
        data["goals"] = [x for x in data["goals"] if int(x.get("id", -1)) != int(goal_id)]
        if len(data["goals"]) == before:
            return False
        _save(data)
        return True

    def add_habit(self, name: str, target_per_week: int = 5) -> dict[str, Any]:
        name = str(name).strip()
        if not name:
            raise ValueError("habit name is required")
        target_per_week = max(1, min(7, int(target_per_week)))
        data = _load()
        item = {"id": self._next_id(data["habits"]), "name": name,
                "target_per_week": target_per_week, "checks": [], "created_at": _now()}
        data["habits"].append(item)
        _save(data)
        return item

    def check_habit(self, habit_id: int, when: datetime | None = None) -> bool:
        data = _load()
        stamp = (when or datetime.now(timezone.utc)).date().isoformat()
        for item in data["habits"]:
            if int(item.get("id", -1)) == int(habit_id):
                if stamp not in item["checks"]:
                    item["checks"].append(stamp)
                    item["checks"] = item["checks"][-365:]
                    _save(data)
                return True
        return False

    def set_skill(self, skill: str, level: int, evidence: str = "") -> bool:
        skill = str(skill).strip()
        if not skill:
            return False
        data = _load()
        data["skills"][skill] = {"level": max(0, min(100, int(level))),
                                 "evidence": evidence.strip(), "updated_at": _now()}
        _save(data)
        return True

    def record_history(self, kind: str, subject: str, value: Any, note: str = "") -> dict[str, Any]:
        data = _load()
        item = {"kind": str(kind), "subject": str(subject), "value": value,
                "note": str(note), "at": _now()}
        data["history"].append(item)
        data["history"] = data["history"][-1000:]
        _save(data)
        return item

    def insights(self) -> dict[str, Any]:
        data = _load()
        active = [x for x in data["goals"] if not x.get("done")]
        weak_skills = sorted(data["skills"].items(), key=lambda kv: kv[1].get("level", 0))[:3]
        habit_rates = []
        for habit in data["habits"]:
            checks = set(habit.get("checks", []))
            recent = [x for x in checks if x in _week_dates()]
            target = max(1, int(habit.get("target_per_week", 1)))
            habit_rates.append({
                "name": habit.get("name", ""),
                "checks_this_week": len(recent),
                "target": target,
                "complete": len(recent) >= target,
            })
        repeated = {}
        for event in data["history"]:
            if event.get("kind") == "mistake":
                key = str(event.get("subject", "")).casefold()
                repeated[key] = repeated.get(key, 0) + 1
        return {
            "active_goals": len(active),
            "active_goal_progress": round(sum(float(x.get("progress", 0)) for x in active) / max(1, len(active)), 1),
            "habits": habit_rates,
            "skills_needing_work": [{"name": name, **value} for name, value in weak_skills],
            "repeated_mistake_areas": sorted(repeated.items(), key=lambda x: x[1], reverse=True)[:5],
            "history_events": len(data["history"]),
        }

    @staticmethod
    def _next_id(items: list[dict[str, Any]]) -> int:
        return max([int(x.get("id", 0)) for x in items] or [0]) + 1


def _week_dates() -> set[str]:
    today = datetime.now(timezone.utc).date()
    return {(today.fromordinal(today.toordinal() - i)).isoformat() for i in range(7)}


def reset() -> None:
    _save({"goals": [], "habits": [], "skills": {}, "history": []})
