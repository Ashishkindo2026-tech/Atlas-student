"""Build bounded context for Atlas reasoning and student workflows."""
from __future__ import annotations

from collections.abc import Iterable, Mapping


def build_context(
    current_prompt: str,
    history: Iterable[Mapping[str, str]] = (),
    memories: Iterable[str] = (),
    *,
    max_history: int = 12,
    max_memories: int = 8,
) -> str:
    """Return deterministic, bounded context without mutating caller data."""
    if not isinstance(current_prompt, str) or not current_prompt.strip():
        raise ValueError("current_prompt must be a non-empty string")
    if max_history < 0 or max_memories < 0:
        raise ValueError("context limits cannot be negative")

    lines = ["[CURRENT]", current_prompt.strip()]
    history_items = list(history)[-max_history:]
    memory_items = list(memories)[-max_memories:]

    if history_items:
        lines.append("[HISTORY]")
        for item in history_items:
            role = str(item.get("role", "unknown")).strip() or "unknown"
            content = str(item.get("content", "")).strip()
            if content:
                lines.append(f"{role}: {content}")

    if memory_items:
        lines.append("[MEMORY]")
        lines.extend(f"- {str(memory).strip()}" for memory in memory_items if str(memory).strip())

    return "\n".join(lines)
