"""Privacy controls for Atlas Student local data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = (ROOT / "memory", ROOT / "goals", ROOT / "tasks", ROOT / "projects.json", ROOT / "user", ROOT / "education" / "student_profile.json")
SENSITIVE_SUFFIXES = {".json", ".log"}


def _safe(path: Path) -> bool:
    path = path.resolve()
    return any(path == item.resolve() or item.resolve() in path.parents for item in ALLOWED)


class PrivacyShield:
    """User-controlled export, deletion and status for local student data."""

    def status(self) -> Dict[str, Any]:
        files = []
        for root in ALLOWED:
            if root.is_file():
                candidates = [root]
            elif root.exists():
                candidates = list(root.rglob("*"))
            else:
                candidates = []
            for path in candidates:
                if path.is_file() and path.suffix in SENSITIVE_SUFFIXES:
                    files.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size})
        return {"local_only": True, "tracked_files": len(files), "files": files}

    def export(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for item in self.status()["files"]:
            path = ROOT / item["path"]
            try:
                result[item["path"]] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                result[item["path"]] = path.read_text(encoding="utf-8", errors="replace")
        return result

    def delete(self, relative_path: str) -> bool:
        target = (ROOT / relative_path).resolve()
        if not _safe(target) or not target.is_file():
            return False
        target.unlink()
        return True

    def redact(self, text: str) -> str:
        """Remove obvious secrets before text is sent to a model or log."""
        import re
        text = re.sub(r"(?i)(api[_ -]?key|password|token|secret)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
        return text
