"""Unified Atlas Student six-phase subsystem.

Phases: memory, reasoning, vision, voice, planning and privacy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from brain.student_reasoning import StudentReasoner
from education.retrieval import retrieve
from student.progress_manager import ProgressManager
from memory.student_memory import StudentMemory
from planning.student_planner import StudentPlanner
from privacy.privacy_shield import PrivacyShield
from vision.vision_client import VisionClient


class AtlasStudentSystem:
    def __init__(self):
        self.memory = StudentMemory()
        self.reasoner = StudentReasoner()
        self.planner = StudentPlanner()
        self.privacy = PrivacyShield()
        self.vision = VisionClient()
        self.progress = ProgressManager()

    def dashboard(self) -> Dict[str, Any]:
        progress = self.progress.data()
        return {
            "phases": {
                "memory": True,
                "reasoning": True,
                "vision": True,
                "voice": True,
                "planning": True,
                "privacy": True,
            },
            "memory_items": len(self.memory.approved()),
            "recent_messages": len(self.memory.recent()),
            "progress": progress,
            "privacy": self.privacy.status(),
        }

    def plan(self, subject: str, minutes: int) -> str:
        blocks = self.planner.build(subject, minutes, retrieve(subject, limit=6), self.progress.data())
        return self.planner.format(subject, minutes, blocks)

    def reason(self, text: str) -> str:
        return self.reasoner.prompt_context(text)

    def remember(self, text: str, approved: bool = False) -> str:
        if not approved:
            return "Memory approval required. Ask the user before saving this to long-term memory."
        return "Saved to long-term memory." if self.memory.remember(text, approved=True) else "Nothing new was saved."

    def vision_file(self, path: str, prompt: str = "Explain this image for a student.") -> str:
        return self.vision.describe(path, prompt)

    def privacy_export_json(self) -> str:
        return json.dumps(self.privacy.export(), indent=2, ensure_ascii=False)

    def handle(self, command: str) -> Optional[str]:
        """Handle explicit six-phase commands; return None for normal chat."""
        text = command.strip()
        lower = text.lower()
        if lower in {"student dashboard", "atlas student dashboard", "student status"}:
            return json.dumps(self.dashboard(), indent=2, ensure_ascii=False)
        if lower.startswith("student reason "):
            return self.reason(text[15:].strip())
        if lower.startswith("student plan "):
            parts = text[13:].strip().split()
            if len(parts) >= 2:
                try:
                    return self.plan(" ".join(parts[:-1]), int(parts[-1]))
                except ValueError:
                    pass
            return "Use: student plan <subject> <minutes>"
        if lower.startswith("student remember "):
            return self.remember(text[17:].strip(), approved=False)
        if lower in {"student privacy", "student privacy status"}:
            return json.dumps(self.privacy.status(), indent=2, ensure_ascii=False)
        if lower == "student export":
            return self.privacy_export_json()
        if lower.startswith("student vision "):
            payload = text[15:].strip().split("|", 1)
            path = payload[0].strip()
            prompt = payload[1].strip() if len(payload) == 2 else "Explain this image for a student."
            try:
                return self.vision_file(path, prompt)
            except Exception as exc:
                return f"Vision error: {exc}"
        return None


system = AtlasStudentSystem()
