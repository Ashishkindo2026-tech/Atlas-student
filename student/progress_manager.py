"""Persistent learning-progress model for Atlas Student.

Progress is intentionally lightweight: Atlas records explicit study signals and
self-reported mastery rather than guessing sensitive or academic facts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

FILE = Path(__file__).resolve().parent / "progress.json"


def _default() -> Dict:
    return {"subjects": {}, "concepts": {}, "sessions": []}


def _load() -> Dict:
    if not FILE.exists():
        return _default()
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _default()
    except (OSError, json.JSONDecodeError):
        return _default()


def _save(data: Dict) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class ProgressManager:
    def record_session(self, subject: str, minutes: int, topic: str = "") -> None:
        data = _load()
        subject = subject.strip()
        if not subject or minutes <= 0:
            return
        data.setdefault("subjects", {}).setdefault(subject, {"minutes": 0, "sessions": 0})
        data["subjects"][subject]["minutes"] += int(minutes)
        data["subjects"][subject]["sessions"] += 1
        data.setdefault("sessions", []).append({"subject": subject, "minutes": int(minutes), "topic": topic.strip()})
        data["sessions"] = data["sessions"][-100:]
        _save(data)

    def set_mastery(self, subject: str, concept: str, mastery: int) -> bool:
        if not subject.strip() or not concept.strip() or not 0 <= int(mastery) <= 100:
            return False
        data = _load()
        key = f"{subject.strip()}::{concept.strip()}"
        data.setdefault("concepts", {})[key] = {
            "subject": subject.strip(), "concept": concept.strip(), "mastery": int(mastery)
        }
        _save(data)
        return True

    def summary(self) -> str:
        data = _load()
        subjects = data.get("subjects", {})
        concepts = data.get("concepts", {})
        lines = ["Learning progress:"]
        if not subjects and not concepts:
            return "No learning progress has been recorded yet."
        for subject, stats in subjects.items():
            lines.append(f"- {subject}: {stats.get('minutes', 0)} minutes across {stats.get('sessions', 0)} sessions")
        for item in concepts.values():
            lines.append(f"- {item['subject']} / {item['concept']}: {item['mastery']}% mastery")
        return "\n".join(lines)

    def data(self) -> Dict:
        return _load()

    def reset(self) -> None:
        _save(_default())
