"""Small cross-process file lock used by Atlas state stores."""
from __future__ import annotations

import os
import time
import threading
from contextlib import contextmanager

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import fcntl
except ImportError:
    fcntl = None


class FileLock:
    """Re-entrant process/thread lock backed by an OS file lock."""
    _guards: dict[str, threading.RLock] = {}
    _guards_lock = threading.Lock()

    def __init__(self, path: str, timeout: float = 10.0, poll: float = 0.05):
        self.path = os.fspath(path) + ".lock" if not str(path).endswith(".lock") else os.fspath(path)
        self.timeout = timeout
        self.poll = poll
        with self._guards_lock:
            self._thread_lock = self._guards.setdefault(self.path, threading.RLock())
        self._handle = None
        self._depth = 0

    def acquire(self):
        if not self._thread_lock.acquire(timeout=self.timeout):
            raise TimeoutError(f"Timed out waiting for Atlas lock: {self.path}")
        if self._depth:
            self._depth += 1
            return self
        start = time.monotonic()
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            self._handle = open(self.path, "a+b")
            while True:
                try:
                    if msvcrt:
                        self._handle.seek(0)
                        msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
                    elif fcntl:
                        fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._depth = 1
                    return self
                except (OSError, BlockingIOError):
                    if time.monotonic() - start >= self.timeout:
                        raise TimeoutError(f"Timed out waiting for Atlas lock: {self.path}")
                    time.sleep(self.poll)
        except Exception:
            if self._handle:
                self._handle.close()
                self._handle = None
            self._thread_lock.release()
            raise

    def release(self):
        if self._depth <= 0:
            raise RuntimeError("Atlas file lock released without acquire")
        self._depth -= 1
        if self._depth == 0 and self._handle:
            try:
                if msvcrt:
                    self._handle.seek(0)
                    msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
                elif fcntl:
                    fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            finally:
                self._handle.close()
                self._handle = None
        self._thread_lock.release()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False


@contextmanager
def locked_path(path: str, timeout: float = 10.0):
    with FileLock(path, timeout=timeout):
        yield
