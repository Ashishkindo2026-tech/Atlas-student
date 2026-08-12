"""Education retrieval and local Ollama context bridge."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Optional

from .document import DocumentChunk, DocumentIndex
from .ingest import list_indexed_books


def load_index() -> DocumentIndex:
    index = DocumentIndex()
    for book in list_indexed_books():
        path = Path(book["stored_text"])
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    data = json.loads(line)
                    # Backward-compatible with indexes created before metadata fields.
                    data.setdefault("class_level", book.get("class"))
                    data.setdefault("subject", book.get("subject"))
                    index.add(DocumentChunk(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
    return index


def retrieve(
    query: str,
    limit: int = 5,
    class_level: Optional[int] = None,
    subject: Optional[str] = None,
) -> List[Dict]:
    return [
        {
            "text": r.chunk.text,
            "page": r.chunk.page,
            "chapter": r.chunk.chapter,
            "section": r.chunk.section,
            "source": r.chunk.source,
            "score": r.score,
            "class_level": r.chunk.class_level,
            "subject": r.chunk.subject,
        }
        for r in load_index().search(
            query, limit=limit, class_level=class_level, subject=subject
        )
    ]


def build_context(
    query: str,
    limit: int = 5,
    class_level: Optional[int] = None,
    subject: Optional[str] = None,
) -> str:
    results = retrieve(query, limit, class_level=class_level, subject=subject)
    if not results:
        return "No indexed education material matched the query."
    blocks = []
    for i, item in enumerate(results, 1):
        location = f"page {item['page']}" if item.get("page") else "unknown page"
        chapter = f" | {item['chapter']}" if item.get("chapter") else ""
        blocks.append(
            f"[Education source {i} | {item['source']} | {location}{chapter}]\n{item['text']}"
        )
    return "\n\n".join(blocks)
