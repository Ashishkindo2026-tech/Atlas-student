"""Small, dependency-free primitives for reliable local Atlas state."""
from contextlib import contextmanager
from pathlib import Path
import os
import threading

_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path):
    key = str(Path(path).resolve())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


@contextmanager
def file_lock(path):
    """Serialize writes to a local file within the Atlas process."""
    lock = _lock_for(path)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def atomic_write_text(path, text):
    """Write text atomically so interruption cannot leave a half-written file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
