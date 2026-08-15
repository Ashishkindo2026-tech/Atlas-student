"""Atlas Student lifecycle, capability registry and offline-first controls."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "student" / "atlas_state.json"

PHASES = {
    1: ("Core Student", ["ai_chat", "basic_memory", "subjects", "notes", "question_solving", "study_planning"]),
    2: ("Student Intelligence", ["progress_tracking", "mistake_tracking", "weak_topic_detection", "goals", "performance_profile"]),
    3: ("Adaptive Learning", ["personalized_explanations", "automatic_revision", "adaptive_questions", "personalized_path", "mastery_tracking"]),
    4: ("Multimodal Atlas", ["image_recognition", "handwriting_analysis", "textbook_understanding", "voice_conversation", "voice_learning"]),
    5: ("Long-Term Atlas", ["long_term_memory", "academic_history", "age_personality", "career_guidance", "years_progress"]),
    6: ("Atlas Ecosystem", ["phone_pc", "optional_sync", "student_controlled_data", "offline_local", "student_to_atlas_transition"]),
}


def _load() -> Dict[str, Any]:
    try: return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {"offline": True, "sync_enabled": False, "student_age": None}


def _save(data: Dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class AtlasLifecycle:
    def status(self) -> Dict[str, Any]:
        state = _load()
        return {"phases": {str(k): {"name": v[0], "capabilities": v[1], "enabled": True} for k, v in PHASES.items()}, "state": state}

    def set_offline(self, enabled: bool = True) -> Dict[str, Any]:
        data = _load(); data["offline"] = bool(enabled); _save(data); return data

    def set_sync(self, enabled: bool = False) -> Dict[str, Any]:
        data = _load(); data["sync_enabled"] = bool(enabled); _save(data); return data

    def set_age(self, age: int) -> Dict[str, Any]:
        if not 5 <= int(age) <= 100: raise ValueError("invalid age")
        data = _load(); data["student_age"] = int(age); _save(data); return data

    def personality_mode(self) -> str:
        age = _load().get("student_age")
        if age is None: return "student"
        if age < 13: return "tutor"
        if age < 17: return "study_strategist"
        if age < 21: return "university_productivity"
        return "professional_planning"

    def local_capability(self) -> bool:
        return _load().get("offline", True) and bool(os.path.isdir(ROOT))
