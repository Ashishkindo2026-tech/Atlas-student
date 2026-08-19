import json
import os
from datetime import datetime

from core.safe_storage import atomic_write_text, file_lock


class GoalManager:
    """Persistent, normalized and process-safe goal storage."""

    def __init__(self):
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
                try:
                    progress = int(item.get("progress", 0) or 0)
                except (TypeError, ValueError):
                    progress = 0
                normalized.append({"text": text, "created_at": item.get("created_at") or datetime.now().isoformat(timespec="seconds"), "progress": max(0, min(100, progress))})
            elif isinstance(item, str) and item.strip():
                normalized.append({"text": item.strip(), "created_at": datetime.now().isoformat(timespec="seconds"), "progress": 0})
        return normalized

    @staticmethod
    def _normalize_completed(items):
        normalized = []
        for item in items if isinstance(items, list) else []:
            text = str(item.get("text", "")).strip() if isinstance(item, dict) else str(item).strip() if isinstance(item, str) else ""
            if text:
                normalized.append({"text": text, "completed_at": item.get("completed_at") if isinstance(item, dict) and item.get("completed_at") else datetime.now().isoformat(timespec="seconds")})
        return normalized

    def load(self):
        with file_lock(self.file):
            try:
                with open(self.file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("goal store must be an object")
                normalized = {"active_goals": self._normalize_active(data.get("active_goals", [])), "completed_goals": self._normalize_completed(data.get("completed_goals", []))}
                if normalized != data:
                    self._save_unlocked(normalized)
                return normalized
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                return {"active_goals": [], "completed_goals": []}

    def _save_unlocked(self, data):
        atomic_write_text(self.file, json.dumps(data, indent=4, ensure_ascii=False))

    def save(self, data):
        with file_lock(self.file):
            self._save_unlocked(data)

    def add_goal(self, goal):
        goal = str(goal).strip()
        if not goal:
            return False
        with file_lock(self.file):
            data = self.load()
            if goal.casefold() in {g["text"].casefold() for g in data["active_goals"]}:
                return False
            data["active_goals"].append({"text": goal, "created_at": datetime.now().isoformat(timespec="seconds"), "progress": 0})
            self._save_unlocked(data)
            return True

    def get_goals(self):
        return self.load()["active_goals"]

    def update_progress(self, goal, progress):
        try:
            progress = int(progress)
        except (TypeError, ValueError):
            return False
        if not 0 <= progress <= 100:
            return False
        with file_lock(self.file):
            data = self.load()
            for item in data["active_goals"]:
                if item["text"].casefold() == str(goal).strip().casefold():
                    item["progress"] = progress
                    self._save_unlocked(data)
                    return True
        return False

    def complete_goal(self, goal):
        with file_lock(self.file):
            data = self.load()
            target = str(goal).strip().casefold()
            for item in list(data["active_goals"]):
                if item["text"].casefold() == target:
                    data["active_goals"].remove(item)
                    data["completed_goals"].append({"text": item["text"], "completed_at": datetime.now().isoformat(timespec="seconds")})
                    self._save_unlocked(data)
                    return True
        return False

    def get_completed_goals(self):
        return self.load()["completed_goals"]

    def summary(self):
        goals = self.get_goals()
        return "No active goals." if not goals else "\n".join(f"- {g['text']} ({g.get('progress', 0)}%)" for g in goals)
