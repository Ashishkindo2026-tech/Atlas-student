"""Centralized filesystem paths for Atlas runtime data.

Keeping runtime paths relative to the application directory prevents Atlas from
breaking when it is launched from a different working directory.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = PROJECT_ROOT / "runtime_data"
MEMORY_ROOT = RUNTIME_ROOT / "memory"
PROJECTS_ROOT = RUNTIME_ROOT / "projects"

MEMORY_FILE = MEMORY_ROOT / "memory.json"
HISTORY_FILE = MEMORY_ROOT / "chat_history.json"
ARCHIVE_FILE = MEMORY_ROOT / "archive.json"
PROJECT_FILE = PROJECTS_ROOT / "projects.json"


def ensure_runtime_dirs():
    for path in (MEMORY_ROOT, PROJECTS_ROOT):
        path.mkdir(parents=True, exist_ok=True)
