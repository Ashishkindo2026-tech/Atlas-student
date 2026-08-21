"""Conservative local model profiles for different hardware tiers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    name: str
    model: str
    context: int
    num_thread: int | None = None


PROFILES = {
    "low-end": ModelProfile("low-end", "qwen2.5:1.5b", 2048, 2),
    "balanced": ModelProfile("balanced", "qwen2.5:1.5b", 4096, 4),
    "high-memory": ModelProfile("high-memory", "qwen2.5:3b", 8192, 8),
}


def select_profile(name: str) -> ModelProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"unknown Atlas hardware profile: {name}") from exc
