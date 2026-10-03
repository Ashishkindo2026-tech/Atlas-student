"""Local Atlas backup and restore for user-owned JSON state.

Backups are explicit, JSON-only, and limited to Atlas data roots. No secrets or
runtime cache directories are included.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOTS = (
    ROOT / "memory",
    ROOT / "student",
    ROOT / "goals",
    ROOT / "user",
    ROOT / "education" / "student_profile.json",
)
EXCLUDED_NAMES = {".env", ".env.local", "chat_history.json", "memory.json"}
SCHEMA = "atlas.local.backup"
VERSION = 1


def _safe_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for root in DEFAULT_ROOTS:
        if root.is_file():
            candidates = [root]
        elif root.exists():
            candidates = list(root.rglob("*.json"))
        else:
            candidates = []
        for path in candidates:
            if path.is_file() and path.name not in EXCLUDED_NAMES and ".tmp" not in path.name:
                files.append(path)
    return sorted(set(files))


def export_bundle(path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {}
    for source in _iter_files():
        rel = _safe_relative(source)
        try:
            files[rel] = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
    from gui.theme_store import load_ui
    bundle = {
        "schema": SCHEMA,
        "version": VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "settings": load_ui(),
        "files": files,
    }
    target.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def validate_bundle(bundle: dict[str, Any]) -> bool:
    return (
        isinstance(bundle, dict)
        and bundle.get("schema") == SCHEMA
        and int(bundle.get("version", -1)) == VERSION
        and isinstance(bundle.get("files"), dict)
        and isinstance(bundle.get("settings", {}), dict)
    )


def restore_bundle(path: str | Path, *, replace: bool = True) -> list[str]:
    source = Path(path).expanduser().resolve()
    bundle = json.loads(source.read_text(encoding="utf-8"))
    if not validate_bundle(bundle):
        raise ValueError("Invalid Atlas backup bundle.")
    restored: list[str] = []
    if "settings" in bundle:
        from gui.theme_store import save_ui
        save_ui(bundle["settings"])
        restored.append("settings/ui.json")
    for rel, value in bundle["files"].items():
        target = (ROOT / rel).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            raise ValueError(f"Backup path escapes Atlas root: {rel}")
        if target.name in EXCLUDED_NAMES or target.suffix.lower() != ".json":
            continue
        if target.exists() and not replace:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, target)
        restored.append(rel)
    return restored
