import json
import os
from datetime import datetime

class GoalManager:
    def __init__(self):
        self.file = "goals/goals.json"
        os.makedirs("goals", exist_ok=True)
        if not os.path.exists(self.file):
            self.save({"active_goals": [], "completed_goals": []})

    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"active_goals": [], "completed_goals": []}
            data.setdefault("active_goals", [])
            data.setdefault("completed_goals", [])
            return data
        except (OSError, json.JSONDecodeError):
            return {"active_goals": [], "completed_goals": []}

    def save(self, data):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_goal(self, goal):
        goal = str(goal).strip()
        if not goal:
            return False
        data = self.load()
        existing = [g.get("text") if isinstance(g, dict) else g for g in data["active_goals"]]
        if goal in existing:
            return False
        data["active_goals"].append({"text": goal, "created_at": datetime.now().isoformat(timespec="seconds"), "progress": 0})
        self.save(data)
        return True

    def get_goals(self):
        return self.load()["active_goals"]

    def update_progress(self, goal, progress):
        data = self.load()
        for item in data["active_goals"]:
            if isinstance(item, dict) and item["text"].lower() == goal.lower():
                item["progress"] = max(0, min(100, int(progress)))
                self.save(data)
                return True
        return False

    def complete_goal(self, goal):
        data = self.load()
        for item in list(data["active_goals"]):
            text = item.get("text") if isinstance(item, dict) else item
            if text.lower() == goal.lower():
                data["active_goals"].remove(item)
                data["completed_goals"].append({"text": text, "completed_at": datetime.now().isoformat(timespec="seconds")})
                self.save(data)
                return True
        return False

    def get_completed_goals(self):
        return self.load()["completed_goals"]

    def summary(self):
        goals = self.get_goals()
        if not goals:
            return "No active goals."
        return "\n".join(f"- {g['text']} ({g.get('progress', 0)}%)" if isinstance(g, dict) else f"- {g}" for g in goals)
