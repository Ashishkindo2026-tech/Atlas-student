"""Phases 31-33: bounded self-extension, self-debugging, capability registry."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import tempfile

from .protected_core import is_protected

LEVELS = {"observe": 0, "suggest": 1, "sandbox": 2, "apply": 3, "autonomous": 4}

@dataclass
class ChangeRecord:
    change_id: str
    date: str
    reason: str
    files: list[str]
    expected_result: str
    risks: list[str]
    tests: list[str]
    result: str
    rollback_point: str

class SelfExtensionEngine:
    def __init__(self, root=".", permission_level=1):
        self.root = Path(root).resolve()
        self.permission_level = permission_level
        self.history_dir = self.root / ".atlas" / "changes"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def can_edit(self, files, requested_level=1):
        return requested_level <= self.permission_level and not any(is_protected(f) for f in files)

    def plan(self, reason, files, expected_result, risks=None):
        return {"reason": reason, "files": list(files), "expected_result": expected_result, "risks": list(risks or [])}

    def snapshot(self, files):
        snap = Path(tempfile.mkdtemp(prefix="atlas-snapshot-"))
        for rel in files:
            src = self.root / rel
            if src.exists():
                dst = snap / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return str(snap)

    def record(self, plan, tests, result, rollback_point):
        cid = datetime.now(timezone.utc).strftime("change-%Y%m%dT%H%M%S%fZ")
        record = ChangeRecord(cid, datetime.now(timezone.utc).isoformat(), plan["reason"], plan["files"], plan["expected_result"], plan["risks"], list(tests), result, rollback_point)
        (self.history_dir / f"{cid}.json").write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
        return record

    def validate(self, files, reason):
        if not reason.strip(): raise ValueError("A clear reason is required")
        if len(files) != len(set(files)): raise ValueError("One change must contain unique files")
        if any(is_protected(f) for f in files): raise PermissionError("Protected change requires human approval")
        return True
