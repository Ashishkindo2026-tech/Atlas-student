"""Persistent, lightweight student learning progress store."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

PROGRESS_FILE = Path(__file__).resolve().parent / "progress.json"


def _load():
    if not PROGRESS_FILE.exists():
        return {"concepts": {}}
    try:
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"concepts": {}}


def _save(data):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def update_concept(class_level: int, subject: str, concept: str, *, mastery: float | None = None,
                   correct: bool | None = None) -> dict:
    if not 1 <= int(class_level) <= 12:
        raise ValueError("class_level must be between 1 and 12")
    data = _load()
    key = f"{int(class_level)}:{subject.strip().lower()}:{concept.strip().lower()}"
    item = data.setdefault("concepts", {}).setdefault(key, {
        "class": int(class_level), "subject": subject, "concept": concept,
        "attempts": 0, "correct": 0, "mastery": 0.0,
    })
    if correct is not None:
        item["attempts"] += 1
        item["correct"] += int(bool(correct))
        item["mastery"] = item["correct"] / item["attempts"]
    if mastery is not None:
        item["mastery"] = max(0.0, min(1.0, float(mastery)))
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)
    return item


def get_progress(class_level: int | None = None, subject: str | None = None):
    items = list(_load().get("concepts", {}).values())
    if class_level is not None:
        items = [x for x in items if x["class"] == int(class_level)]
    if subject is not None:
        items = [x for x in items if x["subject"].lower() == subject.lower()]
    return items


def weak_concepts(class_level: int | None = None, subject: str | None = None, threshold: float = 0.6):
    return [x for x in get_progress(class_level, subject) if x.get("mastery", 0.0) < threshold]
