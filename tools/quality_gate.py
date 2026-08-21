"""Deterministic repository quality gates for Atlas Student.

This checker is intentionally dependency-light so it can run before optional
runtime dependencies are installed. It verifies structural requirements,
forbidden local-state files, empty Python modules, and required test/CI assets.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path

REQUIRED_PATHS = (
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    ".github/workflows/atlas-tests.yml",
    "tests",
    "benchmarks",
    "atlas_core/config.py",
    "llm/ollama_client.py",
)
FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    "memory.json",
    "chat_history.json",
}


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    details: str


def _python_files(root: Path):
    ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    for path in root.rglob("*.py"):
        if not any(part in ignored for part in path.parts):
            yield path


def run_gates(root: Path) -> list[GateResult]:
    results: list[GateResult] = []

    missing = [p for p in REQUIRED_PATHS if not (root / p).exists()]
    results.append(GateResult("required-structure", not missing,
                             "missing: " + ", ".join(missing) if missing else "all required paths exist"))

    empty = [str(p.relative_to(root)) for p in _python_files(root) if p.stat().st_size == 0]
    results.append(GateResult("non-empty-python", not empty,
                             "empty modules: " + ", ".join(empty) if empty else "no empty Python modules"))

    secrets = []
    for path in root.rglob("*"):
        if path.is_file() and path.name in FORBIDDEN_NAMES:
            secrets.append(str(path.relative_to(root)))
    results.append(GateResult("local-state-protection", not secrets,
                             "forbidden local-state files: " + ", ".join(secrets) if secrets else "no forbidden local-state files tracked"))

    tests = root / "tests"
    test_files = list(tests.rglob("test_*.py")) if tests.exists() else []
    results.append(GateResult("automated-test-suite", bool(test_files),
                             f"{len(test_files)} test modules discovered"))

    workflow = root / ".github/workflows/atlas-tests.yml"
    ci_text = workflow.read_text(encoding="utf-8") if workflow.exists() else ""
    ci_ok = "pytest" in ci_text and "python" in ci_text.lower()
    results.append(GateResult("ci-test-command", ci_ok,
                             "CI workflow invokes Python tests" if ci_ok else "CI test command not detected"))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Atlas Student repository quality gates")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_gates(args.root.resolve())
    payload = {"passed": all(r.passed for r in results), "gates": [asdict(r) for r in results]}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            print(f"{'PASS' if result.passed else 'FAIL'}  {result.name}: {result.details}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
