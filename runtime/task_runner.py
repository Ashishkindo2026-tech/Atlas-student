"""Bounded background task execution with safe completion callbacks."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class TaskRunner:
    """Run blocking work without allowing one task to kill the host process.

    A small bounded pool prevents accidental thread explosions. Exceptions are
    returned through the supplied error callback instead of being swallowed.
    """

    def __init__(self, max_workers: int = 2):
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="atlas-worker")
        self._lock = Lock()
        self._closed = False

    def submit(
        self,
        fn: Callable[..., T],
        *args,
        on_success: Optional[Callable[[T], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs,
    ) -> Future:
        with self._lock:
            if self._closed:
                raise RuntimeError("TaskRunner is closed")
            future = self._executor.submit(fn, *args, **kwargs)

        def finish(done: Future) -> None:
            try:
                result = done.result()
            except Exception as exc:  # deliberate boundary: surface failure to caller
                if on_error is not None:
                    on_error(exc)
                return
            if on_success is not None:
                on_success(result)

        future.add_done_callback(finish)
        return future

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=True)
