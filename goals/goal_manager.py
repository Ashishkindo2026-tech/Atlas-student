import json
import os
from datetime import datetime


class GoalManager:
    """Persistent goal storage with legacy-data normalization and test isolation."""

    def __init__(self):
        # Tests can point Atlas at an isolated file without changing production storage.
        self.file = os.environ.get("ATLAS_GOALS_FILE", "goals/goals.json")
        os.makedirs(os.path.dirname(self.file) or ".", exist_ok=True)
        if not os.path.exists(self.file):
            self.save({"active_goals": [], "completed_goals": []})

    @staticmethod
    def _normalize_active(items):
        normalized = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
                if not text:
                    continue
                normalized.append({
                    "text": text,
                    "created_at": item.get("created_at") or datetime.now().isoformat(timespec="seconds"),
                    "progress": max(0, min(100, int(item.get("progress", 0) or 0))),
                })
            elif isinstance(item, str) and item.strip():
                # Migrate old string-only goals into the current schema.
                normalized.append({
                    "text": item.strip(),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "progress": 0,
                })
        return normalized

    @staticmethod
    def _normalize_completed(items):
        normalized = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                text = str(item.get("text", "")).strip()
                if text:
                    normalized.append({
                        "text": text,
                        "completed_at": item.get("completed_at") or datetime.now().isoformat(timespec="seconds"),
                    })
            elif isinstance(item, str) and item.strip():
                normalized.append({
                    "text": item.strip(),
                    "completed_at": datetime.now().isoformat(timespec="seconds"),
                })
        return normalized

    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"active_goals": [], "completed_goals": []}
            normalized = {
                "active_goals": self._normalize_active(data.get("active_goals", [])),
                "completed_goals": self._normalize_completed(data.get("completed_goals", [])),
            }
            # Persist migrations so fresh Atlas instances see the same schema.
            if normalized != data:
                self.save(normalized)
            return normalized
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return {"active_goals": [], "completed_goals": []}

    def save(self, data):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_goal(self, goal):
        goal = str(goal).strip()
        if not goal:
            return False
        data = self.load()
        existing = {g["text"].casefold() for g in data["active_goals"]}
        if goal.casefold() in existing:
            return False
        data["active_goals"].append({
            "text": goal,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "progress": 0,
        })
        self.save(data)
        return True

    def get_goals(self):
        return self.load()["active_goals"]

    def update_progress(self, goal, progress):
        data = self.load()
        try:
            progress = int(progress)
        except (TypeError, ValueError):
            return False
        if not 0 <= progress <= 100:
            return False
        for item in data["active_goals"]:
            if item["text"].casefold() == str(goal).strip().casefold():
                item["progress"] = progress
                self.save(data)
                return True
        return False

    def complete_goal(self, goal):
        data = self.load()
        target = str(goal).strip().casefold()
        for item in list(data["active_goals"]):
            if item["text"].casefold() == target:
                data["active_goals"].remove(item)
                data["completed_goals"].append({
                    "text": item["text"],
                    "completed_at": datetime.now().isoformat(timespec="seconds"),
                })
                self.save(data)
                return True
        return False

    def get_completed_goals(self):
        return self.load()["completed_goals"]

    def summary(self):
        goals = self.get_goals()
        if not goals:
            return "No active goals."
        return "\n".join(f"- {g['text']} ({g.get('progress', 0)}%)" for g in goals)
