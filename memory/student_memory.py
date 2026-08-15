"""Consent-aware student memory for Atlas Student.

This module deliberately keeps short-term conversation separate from approved
long-term facts. All writes are atomic so a power loss cannot leave half a JSON
file behind.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "memory" / "student_memory.json"

DEFAULT = {"version": 1, "long_term": [], "short_term": []}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict[str, Any]:
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {"version": 1, "long_term": list(data.get("long_term", [])), "short_term": list(data.get("short_term", []))}
    except (OSError, json.JSONDecodeError):
        pass
    return dict(DEFAULT)


def _save(data: Dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="atlas-memory-", suffix=".json", dir=str(STORE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, STORE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class StudentMemory:
    """Explicit-consent memory API."""

    def remember(self, content: str, *, approved: bool = False, kind: str = "fact") -> bool:
        content = str(content).strip()
        if not content or not approved:
            return False
        data = _load()
        if any(item.get("content") == content for item in data["long_term"]):
            return False
        data["long_term"].append({"content": content, "kind": kind, "created_at": _now()})
        _save(data)
        return True

    def add_short_term(self, role: str, message: str, limit: int = 40) -> None:
        data = _load()
        data["short_term"].append({"role": role, "message": str(message), "created_at": _now()})
        data["short_term"] = data["short_term"][-max(1, int(limit)):]
        _save(data)

    def approved(self) -> List[Dict[str, Any]]:
        return list(_load()["long_term"])

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(_load()["short_term"][-max(1, int(limit)):])

    def forget(self, query: str) -> int:
        query = str(query).strip().lower()
        data = _load()
        before = len(data["long_term"])
        data["long_term"] = [x for x in data["long_term"] if query not in x.get("content", "").lower()]
        _save(data)
        return before - len(data["long_term"])

    def clear_long_term(self) -> int:
        data = _load()
        count = len(data["long_term"])
        data["long_term"] = []
        _save(data)
        return count

    def export(self) -> Dict[str, Any]:
        return _load()
