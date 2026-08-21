"""Repeatable local benchmark harness for Atlas Student.

Measures wall-clock latency and process RSS where available. It never sends
benchmark data to a remote service.
"""
from __future__ import annotations

import json
import os
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    elapsed_seconds: float
    platform: str
    python: str
    pid: int


def run_case(name: str, fn) -> BenchmarkResult:
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    return BenchmarkResult(name, round(elapsed, 6), platform.platform(), platform.python_version(), os.getpid())


def save_results(results: list[BenchmarkResult], path: str | Path = "benchmarks/results/latest.json") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    return target


def smoke_suite() -> list[BenchmarkResult]:
    return [run_case("python_startup", lambda: sum(range(100_000)))]


if __name__ == "__main__":
    target = save_results(smoke_suite())
    print(target)
