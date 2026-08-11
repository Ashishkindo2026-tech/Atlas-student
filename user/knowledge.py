import json
import os
from datetime import datetime

FILE = "user/user_knowledge.json"

class UserKnowledge:
    """Explicitly learned, non-sensitive facts/preferences about the user."""
    def __init__(self):
        self._ensure()

    def _ensure(self):
        os.makedirs("user", exist_ok=True)
        if not os.path.exists(FILE):
            self.save({"facts": {}, "learning": {}, "preferences": {}})

    def load(self):
        self._ensure()
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {"facts": {}, "learning": {}, "preferences": {}}
        except (OSError, json.JSONDecodeError):
            return {"facts": {}, "learning": {}, "preferences": {}}

    def save(self, data):
        os.makedirs("user", exist_ok=True)
        temp = FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp, FILE)

    def remember(self, category, key, value, source="explicit"):
        data = self.load()
        data.setdefault(category, {})[key] = {
            "value": value,
            "source": source,
            "updated_at": datetime.now().isoformat(timespec="seconds")
        }
        self.save(data)

    def get(self):
        return self.load()

    def summary(self):
        data = self.load()
        lines = []
        for category, items in data.items():
            if items:
                lines.append(f"{category}: {items}")
        return "\n".join(lines) if lines else "No explicit user knowledge stored."

    def reset(self):
        self.save({"facts": {}, "learning": {}, "preferences": {}})
