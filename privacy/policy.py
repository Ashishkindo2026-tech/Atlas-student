"""Local-first privacy controls for Atlas Student."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PrivacyPolicy:
    local_only: bool = True
    allow_network_llm: bool = False
    store_chat_history: bool = True
    store_user_profile: bool = True

    def validate_path(self, path: str | Path, root: str | Path) -> bool:
        """Return True only when a writable data path stays inside root."""
        target = Path(path).resolve()
        base = Path(root).resolve()
        try:
            target.relative_to(base)
            return True
        except ValueError:
            return False


DEFAULT_POLICY = PrivacyPolicy()
