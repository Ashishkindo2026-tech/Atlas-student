"""Education-intelligence orchestration for Atlas Student.

This layer combines the education profile, CBSE core metadata, local retrieval,
and learning evidence without inventing missing student constraints.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

from .cbse_core import CBSECore, CORE_CLASSES
from .retrieval import retrieve
from .student_profile import EducationProfile

_SUBJECT_ALIASES = {
    "math": "Mathematics",
    "mathematics": "Mathematics",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "biology": "Biology",
    "english": "English",
    "science": "Science",
    "social science": "Social Science",
    "history": "History",
    "geography": "Geography",
    "computer science": "Computer Science",
    "computer": "Computer Science",
}


class EducationIntelligence:
    """Build a deterministic education state for a single student request."""

    def __init__(self, profile: Optional[EducationProfile] = None, core: Optional[CBSECore] = None):
        self.profile = profile or EducationProfile()
        self.core = core or CBSECore()

    @staticmethod
    def explicit_class(query: str) -> Optional[int]:
        patterns = (
            r"\bclass\s*(1[0-2]|[1-9])\b",
            r"\bgrade\s*(1[0-2]|[1-9])\b",
            r"\b(?:std|standard)\s*(1[0-2]|[1-9])\b",
        )
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def explicit_subject(query: str) -> Optional[str]:
        lower = query.lower()
        for alias, subject in sorted(_SUBJECT_ALIASES.items(), key=lambda item: -len(item[0])):
            if re.search(rf"\b{re.escape(alias)}\b", lower):
                return subject
        return None

    def analyze(self, query: str, progress: Optional[Dict] = None) -> Dict:
        """Return education state without changing persistent data."""
        query = query.strip()
        profile = self.profile.data()
        class_level = self.explicit_class(query) or profile.get("primary_class")
        subject = self.explicit_subject(query) or profile.get("primary_subject")

        indexed = retrieve(query, limit=6) if query else []
        relevant_signals = []
        if isinstance(progress, dict):
            for signal in progress.get("learning_signals", []):
                if subject and signal.get("subject") and signal["subject"].lower() != subject.lower():
                    continue
                relevant_signals.append(signal)
        relevant_signals = relevant_signals[-20:]

        return {
            "board": profile.get("board", "CBSE"),
            "class_level": class_level,
            "subject": subject,
            "core_curriculum": list(CORE_CLASSES),
            "material_found": bool(indexed),
            "retrieval": indexed,
            "learning_evidence": relevant_signals,
            "needs_class": class_level is None,
            "needs_subject": subject is None,
        }

    @staticmethod
    def prompt_context(state: Dict) -> str:
        lines = [
            "EDUCATION INTELLIGENCE:",
            f"- Board: {state.get('board', 'CBSE')}",
            f"- Class: {state.get('class_level') or 'not explicitly set'}",
            f"- Subject: {state.get('subject') or 'not explicitly set'}",
            "- Core curriculum: Classes 9-12",
            f"- Indexed material found: {'yes' if state.get('material_found') else 'no'}",
        ]
        evidence = state.get("learning_evidence") or []
        if evidence:
            lines.append("- Recent learning evidence:")
            for item in evidence[-5:]:
                lines.append(f"  - {item.get('kind')}: {item.get('evidence')}")
        else:
            lines.append("- Recent learning evidence: none")
        if state.get("retrieval"):
            lines.append("- Retrieved source locations:")
            for item in state["retrieval"][:5]:
                page = item.get("page") or "unknown"
                lines.append(f"  - {item.get('source', 'local source')} | page {page}")
        else:
            lines.append("- Retrieved source locations: none")
        return "\n".join(lines)
