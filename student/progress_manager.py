"""Persistent learning-progress model for Atlas Student.

Progress records explicit study activity, self-reported mastery, and learning
signals. Signals are evidence, not automatic mastery percentages.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

FILE = Path(__file__).resolve().parent / "progress.json"


def _default() -> Dict:
    return {"subjects": {}, "concepts": {}, "sessions": [], "learning_signals": []}


def _load() -> Dict:
    if not FILE.exists():
        return _default()
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default()
        data.setdefault("subjects", {})
        data.setdefault("concepts", {})
        data.setdefault("sessions", [])
        data.setdefault("learning_signals", [])
        return data
    except (OSError, json.JSONDecodeError):
        return _default()


def _save(data: Dict) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class ProgressManager:
    def record_session(self, subject: str, minutes: int, topic: str = "") -> bool:
        data = _load()
        subject = subject.strip()
        if not subject or minutes <= 0:
            return False
        data.setdefault("subjects", {}).setdefault(subject, {"minutes": 0, "sessions": 0})
        data["subjects"][subject]["minutes"] += int(minutes)
        data["subjects"][subject]["sessions"] += 1
        data.setdefault("sessions", []).append({"subject": subject, "minutes": int(minutes), "topic": topic.strip()})
        data["sessions"] = data["sessions"][-100:]
        _save(data)
        return True

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

    def record_learning_signal(self, kind: str, concept: str | None, confidence: float, evidence: str, subject: str | None = None) -> bool:
        if kind not in {"difficulty", "understood"} or not evidence.strip():
            return False
        confidence = max(0.0, min(1.0, float(confidence)))
        data = _load()
        signals = data.setdefault("learning_signals", [])
        signals.append({
            "kind": kind,
            "concept": concept.strip() if concept else None,
            "subject": subject.strip() if subject else None,
            "confidence": confidence,
            "evidence": evidence.strip(),
        })
        data["learning_signals"] = signals[-200:]
        _save(data)
        return True

    def summary(self) -> str:
        data = _load()
        subjects = data.get("subjects", {})
        concepts = data.get("concepts", {})
        signals = data.get("learning_signals", [])
        lines = ["Learning progress:"]
        if not subjects and not concepts and not signals:
            return "No learning progress has been recorded yet."
        for subject, stats in subjects.items():
            lines.append(f"- {subject}: {stats.get('minutes', 0)} minutes across {stats.get('sessions', 0)} sessions")
        for item in concepts.values():
            lines.append(f"- {item['subject']} / {item['concept']}: {item['mastery']}% mastery")
        if signals:
            difficulty = sum(1 for s in signals if s.get("kind") == "difficulty")
            understood = sum(1 for s in signals if s.get("kind") == "understood")
            lines.append(f"- Learning evidence: {understood} understanding, {difficulty} difficulty signals")
        return "\n".join(lines)

    def data(self) -> Dict:
        return _load()

    def reset(self) -> None:
        _save(_default())
