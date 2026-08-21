"""Student progress tracking primitives."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Progress:
    """Track completed learning items with stable, serializable state."""

    completed: set[str] = field(default_factory=set)

    def mark_complete(self, item: str) -> None:
        item = item.strip()
        if not item:
            raise ValueError("item must not be empty")
        self.completed.add(item)

    def is_complete(self, item: str) -> bool:
        return item.strip() in self.completed

    def completion_ratio(self, total_items: int) -> float:
        if total_items <= 0:
            raise ValueError("total_items must be > 0")
        return min(1.0, len(self.completed) / total_items)

    def to_dict(self) -> dict[str, list[str]]:
        return {"completed": sorted(self.completed)}

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        values = data.get("completed", [])
        if not isinstance(values, list):
            raise ValueError("completed must be a list")
        return cls(completed={str(value).strip() for value in values if str(value).strip()})
