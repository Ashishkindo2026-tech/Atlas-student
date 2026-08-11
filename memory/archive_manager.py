import json
import os
from datetime import datetime

FILE = "memory/archive.json"

class ArchiveManager:
    """Moves old memories to an archive instead of destroying them."""
    def __init__(self):
        os.makedirs("memory", exist_ok=True)
        if not os.path.exists(FILE):
            self.save([])

    def load(self):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save(self, data):
        temp = FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp, FILE)

    def archive(self, kind, content, reason="user_requested"):
        data = self.load()
        data.append({
            "kind": kind,
            "content": content,
            "reason": reason,
            "archived_at": datetime.now().isoformat(timespec="seconds")
        })
        self.save(data)

    def search(self, query):
        q = query.lower()
        return [item for item in self.load() if q in str(item.get("content", "")).lower()]

    def get_all(self):
        return self.load()
