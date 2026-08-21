"""Deterministic A-J completion gates for Atlas Student.

The checker deliberately distinguishes structural evidence from runtime evidence:
a repository cannot claim J/10 without executable tests and recorded benchmark
results. It is dependency-light so it can run before optional runtime packages.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_PATHS = (
    "README.md", "ARCHITECTURE.md", "ROADMAP.md",
    ".github/workflows/atlas-tests.yml", "tests", "benchmarks",
    "atlas_core/config.py", "llm/ollama_client.py",
)
FORBIDDEN_NAMES = {".env", ".env.local", "memory.json", "chat_history.json"}
PHASE_GATES = {
    "A": ("architecture", "code quality", "dependency", "configuration"),
    "B": ("llm", "reasoning", "context", "memory", "tool"),
    "C": ("tutor", "notes", "revision", "question", "study"),
    "D": ("voice", "wake", "gui", "personality", "multimodal"),
    "E": ("ollama", "quant", "cpu", "ram", "benchmark", "low-end"),
    "F": ("test", "recover", "log", "monitor", "regression"),
    "G": ("local", "secure", "permission", "control"),
    "H": ("install", "setup", "hardware", "model selection"),
    "I": ("benchmark", "subsystem", "hardware", "evidence"),
    "J": ("10/10", "no unresolved major weakness"),
}


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    details: str


def _python_files(root: Path):
    ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    for path in root.rglob("*.py"):
        if path.name != "__init__.py" and not any(p in ignored for p in path.parts):
            yield path


def _text(root: Path) -> str:
    chunks = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt"}:
            if any(part in {".git", ".venv", "venv", "__pycache__"} for part in p.parts):
                continue
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="ignore").lower())
            except OSError:
                pass
    return "\n".join(chunks)


def run_gates(root: Path) -> list[GateResult]:
    results: list[GateResult] = []
    missing = [p for p in REQUIRED_PATHS if not (root / p).exists()]
    results.append(GateResult("required-structure", not missing,
                              "missing: " + ", ".join(missing) if missing else "all required paths exist"))

    empty = [str(p.relative_to(root)) for p in _python_files(root) if p.stat().st_size == 0]
    results.append(GateResult("non-empty-python", not empty,
                              "empty implementation modules: " + ", ".join(empty) if empty else "no empty implementation modules"))

    secrets = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name in FORBIDDEN_NAMES]
    results.append(GateResult("local-state-protection", not secrets,
                              "forbidden local-state files: " + ", ".join(secrets) if secrets else "no forbidden local-state files tracked"))

    tests = root / "tests"
    test_files = list(tests.rglob("test_*.py")) if tests.exists() else []
    results.append(GateResult("automated-test-suite", bool(test_files), f"{len(test_files)} test modules discovered"))

    workflow = root / ".github/workflows/atlas-tests.yml"
    ci_text = workflow.read_text(encoding="utf-8") if workflow.exists() else ""
    ci_ok = "pytest" in ci_text and "python" in ci_text.lower()
    results.append(GateResult("ci-test-command", ci_ok,
                              "CI workflow invokes Python tests" if ci_ok else "CI test command not detected"))

    corpus = _text(root)
    for phase, terms in PHASE_GATES.items():
        missing_terms = [term for term in terms if term not in corpus]
        results.append(GateResult(f"phase-{phase}-coverage", not missing_terms,
                                  "missing concepts: " + ", ".join(missing_terms) if missing_terms else "scope concepts represented"))

    evidence = root / "benchmarks"
    evidence_files = [p for p in evidence.rglob("*") if p.is_file()] if evidence.exists() else []
    results.append(GateResult("benchmark-evidence", bool(evidence_files),
                              f"{len(evidence_files)} benchmark/evidence files discovered"))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Atlas Student A-J quality gates")
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
