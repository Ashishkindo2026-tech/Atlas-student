import json
import os
from datetime import datetime


class MemoryManager:
    def __init__(self):
        self.file = "memory/memory.json"
        self.archive_file = "memory/archive.json"
        self._initialize()

    def _initialize(self):
        os.makedirs("memory", exist_ok=True)
        for path, default in (
            (self.file, {"facts": {}, "important_memories": []}),
            (self.archive_file, {"memories": [], "facts": []}),
        ):
            if not os.path.exists(path):
                self._write(path, default)
                continue
            try:
                data = self._read(path)
                if not isinstance(data, dict):
                    self._write(path, default)
                else:
                    changed = False
                    for key, value in default.items():
                        if key not in data or not isinstance(data[key], type(value)):
                            data[key] = value
                            changed = True
                    if changed:
                        self._write(path, data)
            except (OSError, ValueError, TypeError):
                self._write(path, default)

    def _read(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, path, data):
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(temp, path)

    def load(self):
        return self._read(self.file)

    def save(self, data):
        self._write(self.file, data)

    def remember(self, key, value):
        data = self.load()
        data["facts"][key] = value
        self.save(data)

    def recall(self, key):
        return self.load()["facts"].get(key)

    def get_facts(self):
        return self.load()["facts"]

    def add_important_memory(self, text):
        text = str(text).strip()
        if not text:
            return False
        data = self.load()
        if text in data["important_memories"]:
            return False
        data["important_memories"].append(text)
        self.save(data)
        return True

    def get_important_memories(self):
        return self.load()["important_memories"]

    def delete_important_memory(self, text):
        data = self.load()
        if text not in data["important_memories"]:
            return False
        data["important_memories"].remove(text)
        self._archive_memory(text, "important_memory")
        self.save(data)
        return True

    def delete_fact(self, key):
        data = self.load()
        if key not in data["facts"]:
            return False
        value = data["facts"].pop(key)
        self._archive_fact(key, value)
        self.save(data)
        return True

    def archive_all(self):
        data = self.load()
        for text in data["important_memories"]:
            self._archive_memory(text, "important_memory")
        for key, value in data["facts"].items():
            self._archive_fact(key, value)
        self._write(self.file, {"facts": {}, "important_memories": []})
        return True

    def delete_all_memory(self):
        return self.archive_all()

    def _archive_memory(self, text, kind):
        archive = self._read(self.archive_file)
        archive.setdefault("memories", []).append({
            "text": text,
            "type": kind,
            "archived_at": datetime.now().isoformat(timespec="seconds"),
        })
        self._write(self.archive_file, archive)

    def _archive_fact(self, key, value):
        archive = self._read(self.archive_file)
        archive.setdefault("facts", []).append({
            "key": key,
            "value": value,
            "archived_at": datetime.now().isoformat(timespec="seconds"),
        })
        self._write(self.archive_file, archive)

    def get_archive(self):
        return self._read(self.archive_file)
