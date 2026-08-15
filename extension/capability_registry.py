"""Phase 33: explicit Atlas capability registry."""
from dataclasses import dataclass, field

@dataclass
class Capability:
    name: str
    enabled: bool = True
    description: str = ""
    risk: str = "low"
    approved: bool = False

class CapabilityRegistry:
    def __init__(self):
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability):
        self._items[capability.name] = capability

    def has(self, name: str) -> bool:
        c = self._items.get(name)
        return bool(c and c.enabled and (c.approved or c.risk == "low"))

    def missing(self, name: str):
        return not self.has(name)

    def list(self):
        return list(self._items.values())
