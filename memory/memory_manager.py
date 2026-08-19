import json
import os
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

try:
    from config.paths import MEMORY_FILE
except ImportError:
    MEMORY_FILE = "memory/memory.json"


class MemoryManager:
    """Unified local memory store for Atlas with safe persistence and migration."""

    SCHEMA_VERSION = 2
    ACTIVE_STATUSES = {"active"}
    STORE_FILE = os.fspath(MEMORY_FILE)
    LEGACY_FILE = "memory/data.json"

    def __init__(self, file_path=None):
        self.file = os.fspath(file_path or self.STORE_FILE)
        self._initialize()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _default_store():
        return {"version": MemoryManager.SCHEMA_VERSION, "memories": []}

    def _initialize(self):
        os.makedirs(os.path.dirname(self.file) or ".", exist_ok=True)
        if not os.path.exists(self.file):
            self._write(self.file, self._default_store())
        self._migrate()

    def _read(self, path):
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, path, data):
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)

    def _migrate(self):
        try:
            data = self._read(self.file)
        except (OSError, ValueError, TypeError):
            # Preserve corrupt runtime state for diagnosis/recovery.
            if os.path.exists(self.file):
                backup = self.file + ".corrupt"
                try:
                    os.replace(self.file, backup)
                except OSError:
                    pass
            data = self._default_store()

        if isinstance(data, dict) and isinstance(data.get("memories"), list):
            changed = data.get("version") != self.SCHEMA_VERSION
            data["version"] = self.SCHEMA_VERSION
            for memory in data["memories"]:
                before = dict(memory) if isinstance(memory, dict) else {}
                self._normalize_record(memory)
                changed = changed or memory != before
            if changed:
                self._write(self.file, data)
            return

        migrated = self._default_store()
        if isinstance(data, dict):
            for key, value in (data.get("facts") or {}).items():
                migrated["memories"].append(
                    self._new_record("fact", value, key=str(key), importance=0.8, source="legacy_memory")
                )
            for text in data.get("important_memories") or []:
                migrated["memories"].append(
                    self._new_record("important", str(text), importance=0.9, source="legacy_memory")
                )

        if os.path.exists(self.LEGACY_FILE):
            try:
                legacy = self._read(self.LEGACY_FILE)
            except (OSError, ValueError, TypeError):
                legacy = {}
            if isinstance(legacy, dict):
                existing_keys = {m.get("key") for m in migrated["memories"] if m.get("key")}
                for key, value in legacy.items():
                    if str(key) not in existing_keys:
                        migrated["memories"].append(
                            self._new_record("fact", value, key=str(key), importance=0.8, source="legacy_data")
                        )

        self._write(self.file, migrated)

    def _normalize_record(self, record):
        if not isinstance(record, dict):
            return
        now = self._now()
        record.setdefault("id", uuid.uuid4().hex)
        record.setdefault("type", "note")
        record.setdefault("content", "")
        record.setdefault("key", None)
        record.setdefault("value", record.get("content"))
        record.setdefault("importance", 0.5)
        record.setdefault("confidence", 1.0)
        record.setdefault("status", "active")
        record.setdefault("created_at", now)
        record.setdefault("updated_at", record["created_at"])
        record.setdefault("last_accessed_at", None)
        record.setdefault("access_count", 0)
        record.setdefault("source", "atlas")
        record.setdefault("tags", [])
        record.setdefault("related_ids", [])
        return record

    def _new_record(self, memory_type, content, key=None, value=None, importance=0.5,
                    confidence=1.0, source="atlas", tags=None, related_ids=None):
        now = self._now()
        return {
            "id": uuid.uuid4().hex,
            "type": memory_type,
            "content": str(content).strip(),
            "key": key,
            "value": content if value is None else value,
            "importance": max(0.0, min(1.0, float(importance))),
            "confidence": max(0.0, min(1.0, float(confidence))),
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "last_accessed_at": None,
            "access_count": 0,
            "source": source,
            "tags": list(tags or []),
            "related_ids": list(related_ids or []),
        }

    def load(self):
        self._migrate()
        return self._read(self.file)

    def save(self, data):
        if not isinstance(data, dict):
            raise TypeError("Memory store must be a dictionary")
        data["version"] = self.SCHEMA_VERSION
        data.setdefault("memories", [])
        self._write(self.file, data)

    def _active(self):
        return [m for m in self.load()["memories"] if m.get("status") in self.ACTIVE_STATUSES]

    def _persist_record(self, record):
        data = self.load()
        records = data["memories"]
        for index, existing in enumerate(records):
            if existing.get("id") == record.get("id"):
                records[index] = record
                break
        else:
            records.append(record)
        self.save(data)

    @staticmethod
    def _touch(record):
        record["last_accessed_at"] = MemoryManager._now()
        record["access_count"] = int(record.get("access_count", 0)) + 1
        record["updated_at"] = record["last_accessed_at"]

    @staticmethod
    def _similarity(a, b):
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

    def search(self, query, limit=10, include_archived=False):
        query = str(query or "").strip()
        if not query:
            return []
        candidates = self.load()["memories"]
        if not include_archived:
            candidates = [m for m in candidates if m.get("status") in self.ACTIVE_STATUSES]

        tokens = {token for token in re.findall(r"\w+", query.lower()) if len(token) > 1}
        scored = []
        for record in candidates:
            text = " ".join([
                str(record.get("content", "")),
                str(record.get("key", "")),
                " ".join(map(str, record.get("tags", []))),
            ]).lower()
            overlap = sum(1 for token in tokens if token in text)
            similarity = self._similarity(query.lower(), text)
            score = overlap + similarity + float(record.get("importance", 0)) * 0.5
            item = dict(record)
            item["score"] = score
            scored.append(item)

        scored.sort(key=lambda item: (item["score"], item.get("importance", 0)), reverse=True)
        selected_ids = {item.get("id") for item in scored[:limit]}
        if selected_ids:
            data = self.load()
            changed = False
            for record in data["memories"]:
                if record.get("id") in selected_ids:
                    self._touch(record)
                    changed = True
            if changed:
                self.save(data)
        return scored[:limit]
