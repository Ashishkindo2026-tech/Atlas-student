"""Local PDF ingestion pipeline for Atlas Student.

Designed for user-provided or otherwise authorized PDFs. The original PDF is
not copied into the Git repository. Extracted text is stored locally and can
be removed after indexing if the user chooses.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List

from .document import DocumentChunk

LIBRARY_ROOT = Path(__file__).resolve().parent / "library"
INDEX_ROOT = Path(__file__).resolve().parent / "index"
MANIFEST_FILE = INDEX_ROOT / "manifest.json"


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip()).strip("_") or "book"


def _book_id(pdf_path: Path) -> str:
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()[:16]
    return f"{_safe_name(pdf_path.stem)}-{digest}"


def _load_manifest() -> Dict:
    if not MANIFEST_FILE.exists():
        return {"books": {}}
    try:
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"books": {}}


def _save_manifest(data: Dict) -> None:
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _looks_like_heading(text: str) -> bool:
    """Conservative chapter/section heading heuristic for ordinary PDFs."""
    clean = " ".join(text.split())
    if not clean or len(clean) > 120:
        return False
    return bool(re.match(
        r"^(chapter\s+\d+|unit\s+\d+|lesson\s+\d+|\d+(?:\.\d+)*\s+[A-Z][A-Za-z0-9 :,'-]+)$",
        clean,
        flags=re.IGNORECASE,
    ))


def extract_pdf_chunks(
    pdf_path: Path,
    source: str = "user-provided PDF",
    class_level: int | None = None,
    subject: str | None = None,
) -> List[DocumentChunk]:
    """Extract page chunks and attach conservative chapter/section metadata."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PDF ingestion requires PyMuPDF. Install with: pip install pymupdf") from exc

    chunks: List[DocumentChunk] = []
    current_chapter = None
    current_section = None
    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if not text:
                continue

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            for line in lines[:12]:
                if re.match(r"^(chapter\s+\d+|unit\s+\d+|lesson\s+\d+)", line, re.I):
                    current_chapter = line
                    current_section = None
                    break
                if _looks_like_heading(line):
                    current_section = line
                    break

            chunks.append(DocumentChunk(
                text=text,
                page=page_number,
                chapter=current_chapter,
                section=current_section,
                source=source,
                class_level=class_level,
                subject=subject,
            ))
    return chunks


def ingest_pdf(pdf_path: str | Path, class_level: int, subject: str, title: str | None = None) -> Dict:
    """Index a local PDF without copying the original into the repository."""
    path = Path(pdf_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError("pdf_path must point to an existing .pdf file")
    if class_level not in (9, 10, 11, 12):
        raise ValueError("Core ingestion supports Classes 9-12")

    book_id = _book_id(path)
    chunks = extract_pdf_chunks(
        path,
        source=f"{class_level}:{subject}",
        class_level=class_level,
        subject=subject,
    )
    book_dir = INDEX_ROOT / _safe_name(str(class_level)) / _safe_name(subject) / book_id
    book_dir.mkdir(parents=True, exist_ok=True)

    text_path = book_dir / "content.jsonl"
    with text_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps({
                "text": chunk.text,
                "page": chunk.page,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "source": chunk.source,
                "class_level": chunk.class_level,
                "subject": chunk.subject,
            }, ensure_ascii=False) + "\n")

    metadata = {
        "id": book_id,
        "title": title or path.stem,
        "class": class_level,
        "subject": subject,
        "original_path": str(path),
        "stored_text": str(text_path),
        "pages_indexed": len(chunks),
    }
    manifest = _load_manifest()
    manifest.setdefault("books", {})[book_id] = metadata
    _save_manifest(manifest)
    return metadata


def list_indexed_books() -> List[Dict]:
    return list(_load_manifest().get("books", {}).values())


def remove_indexed_book(book_id: str) -> bool:
    """Remove Atlas's extracted/indexed copy; never deletes the original PDF."""
    import shutil

    manifest = _load_manifest()
    metadata = manifest.get("books", {}).pop(book_id, None)
    if not metadata:
        return False
    stored = Path(metadata["stored_text"])
    book_dir = stored.parent
    if book_dir.exists():
        shutil.rmtree(book_dir)
    _save_manifest(manifest)
    return True
