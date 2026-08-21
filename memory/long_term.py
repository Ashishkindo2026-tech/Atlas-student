"""Compatibility facade for Atlas Student long-term memory.

The canonical implementation lives in :mod:`memory.memory_manager`. This
facade keeps the older module path usable without creating a second store.
"""
from __future__ import annotations

from memory.memory_manager import MemoryManager


class LongTermMemory(MemoryManager):
    """Named compatibility class backed by the unified memory manager."""

    pass


__all__ = ["LongTermMemory", "MemoryManager"]
