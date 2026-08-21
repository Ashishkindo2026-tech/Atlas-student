"""Small, dependency-light web-search abstraction for Atlas Student.

The default implementation is deliberately disabled so Atlas remains
local-first. Applications can inject a search callable when network access is
explicitly enabled by the surrounding policy.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


class WebSearch:
    """Policy-aware search facade with injectable backends."""

    def __init__(self, backend: Callable[[str], Any] | None = None, *, allow_network: bool = False) -> None:
        self.backend = backend
        self.allow_network = bool(allow_network)

    def search(self, query: str) -> Any:
        query = str(query).strip()
        if not query:
            raise ValueError("query must not be empty")
        if self.backend is None or not self.allow_network:
            raise RuntimeError("web search is disabled by the local-first policy")
        return self.backend(query)

    def available(self) -> bool:
        return self.backend is not None and self.allow_network


def search(query: str, backend: Callable[[str], Any] | None = None) -> Any:
    """Explicit opt-in convenience API for an injected search backend."""
    return WebSearch(backend, allow_network=backend is not None).search(query)


__all__ = ["WebSearch", "search"]
