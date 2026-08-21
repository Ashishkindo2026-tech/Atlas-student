"""Small standard-library observability layer for Atlas."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Iterator


LOGGER = logging.getLogger("atlas")


def configure_logging(level: int = logging.INFO) -> None:
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        LOGGER.addHandler(handler)
    LOGGER.setLevel(level)


@contextmanager
def timed(operation: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    except Exception:
        LOGGER.exception("operation failed: %s", operation)
        raise
    finally:
        LOGGER.info("operation=%s elapsed=%.4fs", operation, time.perf_counter() - start)
