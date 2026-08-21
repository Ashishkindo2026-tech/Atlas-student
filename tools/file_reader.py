"""Safe text-file reader used by Atlas Student tools."""
from __future__ import annotations

from pathlib import Path


class FileReader:
    """Read UTF-8 text files with an optional byte-size safety limit."""

    def __init__(self, max_bytes: int = 2_000_000) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = int(max_bytes)

    def read(self, path: str | Path) -> str:
        target = Path(path)
        size = target.stat().st_size
        if size > self.max_bytes:
            raise ValueError(f"file exceeds the {self.max_bytes} byte limit")
        return target.read_text(encoding="utf-8")

    def read_lines(self, path: str | Path) -> list[str]:
        return self.read(path).splitlines()


def read_text(path: str | Path, max_bytes: int = 2_000_000) -> str:
    """Convenience wrapper around :class:`FileReader`."""
    return FileReader(max_bytes=max_bytes).read(path)


__all__ = ["FileReader", "read_text"]
