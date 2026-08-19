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
    """Unified local memory store for Atlas.

    All durable memories live in one JSON store. Facts, important memories,
    experiences, and archived memories are records in the same collection.
    Legacy memory/data.json and the old memory.json shape are migrated on load.
    """

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
        for index, existing in enumerate(data["memories"]):
            if existing.get("id") == record.get("id"):
                data["memories"][index] = record
                self.save(data)
                return record
        data["memories"].append(record)
        self.save(data)
        return record

    def remember(self, key, value, confidence=1.0, importance=0.8, source="atlas"):
        key = str(key).strip()
        value = str(value).strip()
        if not key or not value:
            return False

        data = self.load()
        existing = next((m for m in data["memories"]
                         if m.get("key") == key and m.get("status") in self.ACTIVE_STATUSES), None)
        if existing:
            if str(existing.get("value")) == value:
                self._touch(existing)
                self._persist_record(existing)
                return existing
            existing["status"] = "superseded"
            existing["updated_at"] = self._now()
            self._persist_record(existing)

        record = self._new_record("fact", value, key=key, value=value,
                                  confidence=confidence, importance=importance, source=source)
        return self._persist_record(record)

    def recall(self, key):
        key = str(key).strip()
        matches = [m for m in self._active() if m.get("key") == key]
        if not matches:
            return None
        record = max(matches, key=lambda m: m.get("updated_at", ""))
        self._touch(record)
        self._persist_record(record)
        return record.get("value")

    def get_facts(self):
        return {m["key"]: m.get("value") for m in self._active() if m.get("type") == "fact" and m.get("key")}

    def add_important_memory(self, text, importance=0.9, confidence=1.0, source="user_approved"):
        text = str(text).strip()
        if not text:
            return False
        data = self.load()
        candidates = [m for m in data["memories"] if m.get("status") in self.ACTIVE_STATUSES]
        duplicate = next((m for m in candidates if m.get("content", "").casefold() == text.casefold()), None)
        if duplicate:
            self._touch(duplicate)
            self._persist_record(duplicate)
            return duplicate
        record = self._new_record("important", text, importance=importance,
                                  confidence=confidence, source=source)
        return self._persist_record(record)

    def get_important_memories(self):
        return [m["content"] for m in self._active() if m.get("type") == "important"]

    @staticmethod
    def _touch(record):
        record["last_accessed_at"] = MemoryManager._now()
        record["access_count"] = int(record.get("access_count", 0)) + 1

    @staticmethod
    def _tokens(text):
        return {w for w in re.findall(r"[a-z0-9]+", str(text).lower()) if len(w) > 2}

    def _score(self, query, record):
        query_tokens = self._tokens(query)
        if not query_tokens:
            return 0.0
        searchable = " ".join([
            str(record.get("content", "")),
            str(record.get("key") or "").replace("_", " "),
            str(record.get("value") or ""),
            " ".join(record.get("tags") or []),
        ])
        tokens = self._tokens(searchable)
        overlap = len(query_tokens & tokens) / max(1, len(query_tokens))
        phrase = 1.0 if str(query).strip().lower() in searchable.lower() else 0.0
        return round((overlap * 0.65) + (phrase * 0.20) +
                     (float(record.get("importance", 0.5)) * 0.10) +
                     (float(record.get("confidence", 1.0)) * 0.05), 6)

    def search(self, query, limit=10, include_archived=False):
        records = self.load()["memories"]
        if not include_archived:
            records = [m for m in records if m.get("status") in self.ACTIVE_STATUSES]
        scored = []
        for record in records:
            score = self._score(query, record)
            if score > 0:
                item = dict(record)
                item["score"] = score
                scored.append(item)
        scored.sort(key=lambda item: (item["score"], item.get("importance", 0)), reverse=True)

        # Touch the actual stored records, not the transient result copies.
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

    @staticmethod
    def _similar(a, b):
        return SequenceMatcher(None, a.casefold(), b.casefold()).ratio()

    def archive(self, record_id, reason="archived"):
        data = self.load()
        for record in data["memories"]:
            if record.get("id") == record_id and record.get("status") != "archived":
                record["status"] = "archived"
                record["archive_reason"] = reason
                record["updated_at"] = self._now()
                self.save(data)
                return True
        return False

    def archive_matching(self, query, reason="user_requested_forget"):
        data = self.load()
        matches = []
        for record in data["memories"]:
            if record.get("status") not in self.ACTIVE_STATUSES:
                continue
            searchable = f"{record.get('content', '')} {record.get('key') or ''} {record.get('value') or ''}"
            if query.casefold() in searchable.casefold() or self._similar(query, str(record.get("content", ""))) >= 0.72:
                record["status"] = "archived"
                record["archive_reason"] = reason
                record["updated_at"] = self._now()
                matches.append(record)
        self.save(data)
        return matches

    def archive_all(self, reason="user_requested_forget_all"):
        data = self.load()
        count = 0
        for record in data["memories"]:
            if record.get("status") in self.ACTIVE_STATUSES:
                record["status"] = "archived"
                record["archive_reason"] = reason
                record["updated_at"] = self._now()
                count += 1
        self.save(data)
        return count

    def delete_important_memory(self, text):
        matches = self.archive_matching(text, "user_requested_forget")
        return any(m.get("type") == "important" for m in matches)

    def delete_fact(self, key):
        matches = self.archive_matching(str(key), "user_requested_forget")
        return any(m.get("key") == key for m in matches)

    def delete_all_memory(self):
        return self.archive_all()

    def get_archive(self):
        return {"items": [m for m in self.load()["memories"] if m.get("status") == "archived"]}

    def get_all_records(self, include_archived=True):
        records = self.load()["memories"]
        return records if include_archived else [m for m in records if m.get("status") in self.ACTIVE_STATUSES]
