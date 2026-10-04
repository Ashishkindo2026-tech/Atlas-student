"""Small dependency-safe service registry for Atlas's local ecosystem."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ServiceStatus:
    name: str
    ok: bool
    detail: str


class ServiceRegistry:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], Any]] = {}
        self._states: dict[str, ServiceStatus] = {}

    def register(self, name: str, check: Callable[[], Any]) -> None:
        clean = str(name).strip()
        if not clean:
            raise ValueError("service name is required")
        self._checks[clean] = check

    def check(self, name: str) -> ServiceStatus:
        clean = str(name).strip()
        checker = self._checks.get(clean)
        if checker is None:
            status = ServiceStatus(clean, False, "not registered")
        else:
            try:
                result = checker()
                ok = bool(result)
                detail = "ready" if ok else "unavailable"
                status = ServiceStatus(clean, ok, detail)
            except Exception as exc:
                status = ServiceStatus(clean, False, f"{type(exc).__name__}: {exc}")
        self._states[clean] = status
        return status

    def check_all(self) -> dict[str, ServiceStatus]:
        for name in self._checks:
            self.check(name)
        return dict(self._states)

    def status(self) -> dict[str, dict[str, str | bool]]:
        return {name: {"ok": value.ok, "detail": value.detail} for name, value in self._states.items()}
