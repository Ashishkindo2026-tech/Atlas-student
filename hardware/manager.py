"""Hardware abstraction layer for Atlas.

This layer deliberately contains no device-specific implementation. It lets
future phone, wearable, display, audio, or sensor adapters plug into Atlas
without coupling the brain to hardware APIs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class HardwarePermission:
    capability: str
    allowed: bool = False


class Device(Protocol):
    name: str
    capability: str

    def execute(self, action: str, **kwargs: Any) -> Any: ...


class HardwareManager:
    def __init__(self):
        self._devices: dict[str, Device] = {}
        self._permissions: dict[str, bool] = {}

    def register(self, device: Device) -> None:
        self._devices[device.name] = device
        self._permissions.setdefault(device.capability, False)

    def set_permission(self, capability: str, allowed: bool) -> None:
        self._permissions[capability] = bool(allowed)

    def has_permission(self, capability: str) -> bool:
        return self._permissions.get(capability, False)

    def execute(self, device_name: str, action: str, **kwargs: Any) -> Any:
        device = self._devices.get(device_name)
        if device is None:
            raise KeyError(f"Unknown hardware device: {device_name}")
        if not self.has_permission(device.capability):
            raise PermissionError(f"Hardware capability '{device.capability}' is not permitted")
        return device.execute(action, **kwargs)

    def devices(self) -> list[str]:
        return sorted(self._devices)
