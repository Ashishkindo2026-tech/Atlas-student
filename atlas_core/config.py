"""Central configuration for Atlas Student.

All environment-sensitive runtime settings live here so application modules do
not need hard-coded URLs, model names, or filesystem locations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AtlasConfig:
    """Immutable runtime configuration with safe local defaults."""

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:1.5b"
    history_limit: int = 50
    request_timeout_seconds: float = 120.0
    library_dir: Path = PROJECT_ROOT / "education" / "library"

    @classmethod
    def from_environment(cls) -> "AtlasConfig":
        """Build configuration from environment variables with sane defaults."""
        history_limit = int(os.getenv("ATLAS_HISTORY_LIMIT", "50"))
        timeout = float(os.getenv("ATLAS_REQUEST_TIMEOUT", "120"))
        if history_limit < 1:
            raise ValueError("ATLAS_HISTORY_LIMIT must be >= 1")
        if timeout <= 0:
            raise ValueError("ATLAS_REQUEST_TIMEOUT must be > 0")

        return cls(
            ollama_base_url=os.getenv("ATLAS_OLLAMA_URL", cls.ollama_base_url),
            ollama_model=os.getenv("ATLAS_OLLAMA_MODEL", cls.ollama_model),
            history_limit=history_limit,
            request_timeout_seconds=timeout,
            library_dir=Path(os.getenv("ATLAS_LIBRARY_DIR", str(cls.library_dir))),
        )


CONFIG = AtlasConfig.from_environment()
