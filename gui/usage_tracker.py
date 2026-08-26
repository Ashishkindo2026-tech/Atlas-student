"""Local, privacy-first Atlas usage timing for the customization offer.

Atlas does not interrupt a student's first-day experience with a setup wizard.
After seven days of use it can offer Atlas Studio once. All state stays under
APPDATA and contains no conversation or learning data.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
USAGE_FILE = APPDATA / "usage.json"
OFFER_AFTER_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load() -> dict:
    try:
        if USAGE_FILE.exists():
            data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _save(data: dict) -> None:
    APPDATA.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_launch(now: datetime | None = None) -> dict:
    """Record one Atlas launch and return the local usage state."""
    current = now or _now()
    data = _load()
    if not data.get("first_seen"):
        data["first_seen"] = current.isoformat()
    data["last_seen"] = current.isoformat()
    data["launches"] = int(data.get("launches", 0)) + 1
    data.setdefault("customization_offer_shown", False)
    _save(data)
    return data


def days_used(now: datetime | None = None) -> int:
    """Return completed days since Atlas was first used."""
    data = _load()
    raw = data.get("first_seen")
    if not raw:
        return 0
    try:
        first = datetime.fromisoformat(raw)
        current = now or _now()
        return max(0, int((current - first).total_seconds() // 86400))
    except (ValueError, TypeError):
        return 0


def should_offer_customization(now: datetime | None = None) -> bool:
    """Whether the one-time week-one Studio offer should be displayed."""
    data = _load()
    return days_used(now) >= OFFER_AFTER_DAYS and not bool(data.get("customization_offer_shown"))


def mark_offer_shown() -> None:
    """Prevent the week-one offer from becoming an annoying repeated popup."""
    data = _load()
    data["customization_offer_shown"] = True
    _save(data)


def reset_usage_for_testing() -> None:
    """Delete usage state; intended for local development/testing only."""
    try:
        USAGE_FILE.unlink()
    except FileNotFoundError:
        pass
