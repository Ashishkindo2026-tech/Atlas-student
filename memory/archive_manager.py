from memory.memory_manager import MemoryManager


class ArchiveManager:
    """Compatibility facade over the unified MemoryManager archive."""

    def __init__(self, memory_manager=None):
        self.memory = memory_manager or MemoryManager()

    def load(self):
        return self.get_all()

    def save(self, data):
        # Kept for compatibility. Archive writes are now owned by MemoryManager.
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = data if isinstance(data, list) else []
        store = self.memory.load()
        existing = {item.get("id") for item in store["memories"]}
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("id") in existing:
                continue
            item = dict(item)
            item.setdefault("id", __import__("uuid").uuid4().hex)
            item.setdefault("type", item.get("kind", "note"))
            item.setdefault("content", item.get("content", item.get("text", "")))
            item["status"] = "archived"
            item.setdefault("importance", 0.5)
            item.setdefault("confidence", 1.0)
            item.setdefault("created_at", item.get("archived_at", self.memory._now()))
            item.setdefault("updated_at", item.get("archived_at", self.memory._now()))
            item.setdefault("access_count", 0)
            item.setdefault("tags", [])
            item.setdefault("related_ids", [])
            store["memories"].append(item)
        self.memory.save(store)

    def archive(self, kind, content, reason="user_requested"):
        record = self.memory.add_important_memory(
            str(content), importance=0.5, confidence=1.0, source=f"archive:{kind}"
        )
        if record:
            self.memory.archive(record["id"], reason)

    def search(self, query):
        return [item for item in self.get_all().get("items", [])
                if query.casefold() in str(item.get("content", "")).casefold()]

    def get_all(self):
        return self.memory.get_archive()
