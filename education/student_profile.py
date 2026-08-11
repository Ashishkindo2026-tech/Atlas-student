"""Persistent education profile for Atlas Student.

The profile describes the education contract Atlas should follow. It stores
configuration and preferences, not textbook content. Class 9-12 is the core
supported curriculum; Classes 1-8 remain optional user-provided material.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

FILE = Path(__file__).resolve().parent / "student_profile.json"

DEFAULT_PROFILE = {
    "board": "CBSE",
    "core_classes": [9, 10, 11, 12],
    "optional_classes": [1, 2, 3, 4, 5, 6, 7, 8],
    "primary_class": None,
    "primary_subject": None,
    "teaching_mode": "adaptive",
    "source_policy": "prefer indexed CBSE/NCERT material when available",
}


def _load() -> Dict:
    if not FILE.exists():
        return dict(DEFAULT_PROFILE)
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULT_PROFILE)
        profile = dict(DEFAULT_PROFILE)
        profile.update(data)
        return profile
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_PROFILE)


def _save(data: Dict) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class EducationProfile:
    """Student-specific education configuration used by the Atlas agent."""

    def data(self) -> Dict:
        return _load()

    def set_class(self, class_level: int) -> bool:
        class_level = int(class_level)
        if not 1 <= class_level <= 12:
            return False
        data = _load()
        data["primary_class"] = class_level
        _save(data)
        return True

    def set_subject(self, subject: str) -> bool:
        subject = subject.strip()
        if not subject:
            return False
        data = _load()
        data["primary_subject"] = subject
        _save(data)
        return True

    def set_board(self, board: str) -> bool:
        board = board.strip()
        if not board:
            return False
        data = _load()
        data["board"] = board
        _save(data)
        return True

    def context(self) -> str:
        data = _load()
        cls = data.get("primary_class")
        subject = data.get("primary_subject")
        class_text = str(cls) if cls else "not set"
        subject_text = subject or "not set"
        return (
            "EDUCATION PROFILE:\n"
            f"- Board: {data.get('board', 'CBSE')}\n"
            f"- Primary class: {class_text}\n"
            f"- Primary subject: {subject_text}\n"
            "- Core curriculum: Classes 9-12\n"
            "- Classes 1-8: optional user-provided material\n"
            f"- Teaching mode: {data.get('teaching_mode', 'adaptive')}\n"
            f"- Source policy: {data.get('source_policy', DEFAULT_PROFILE['source_policy'])}"
        )

    def reset(self) -> None:
        _save(dict(DEFAULT_PROFILE))
