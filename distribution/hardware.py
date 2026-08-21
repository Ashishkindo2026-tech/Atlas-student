"""Hardware capability detection used for safe model selection."""
from __future__ import annotations

import os
import platform


def cpu_count() -> int:
    return os.cpu_count() or 1


def recommend_profile(ram_gb: float | None = None) -> str:
    """Return a conservative runtime profile without downloading anything."""
    if ram_gb is None:
        return "balanced"
    if ram_gb < 8:
        return "low-end"
    if ram_gb < 16:
        return "balanced"
    return "high-memory"


def hardware_snapshot() -> dict[str, str | int]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": cpu_count(),
    }
