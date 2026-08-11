"""Automatic importer for PDFs dropped into education/library/core."""
from __future__ import annotations

from pathlib import Path
from .ingest import ingest_pdf, LIBRARY_ROOT

CORE_ROOT = LIBRARY_ROOT / "core"


def scan_and_ingest() -> list[dict]:
    results = []
    if not CORE_ROOT.exists():
        return results
    for pdf in CORE_ROOT.rglob("*.pdf"):
        relative = pdf.relative_to(CORE_ROOT)
        parts = relative.parts
        if len(parts) < 3:
            continue
        try:
            class_level = int(parts[0].replace("class", ""))
        except ValueError:
            continue
        subject = parts[1]
        try:
            results.append(ingest_pdf(pdf, class_level, subject))
        except Exception as exc:
            results.append({"path": str(pdf), "error": str(exc)})
    return results
