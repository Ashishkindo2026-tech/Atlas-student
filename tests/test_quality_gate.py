from pathlib import Path

from tools.quality_gate import run_gates


def test_repository_quality_gates_pass():
    root = Path(__file__).resolve().parents[1]
    results = run_gates(root)
    failures = [result for result in results if not result.passed]
    assert not failures, "\n".join(f"{r.name}: {r.details}" for r in failures)


def test_required_paths_are_explicit():
    root = Path(__file__).resolve().parents[1]
    results = {result.name: result for result in run_gates(root)}
    assert results["required-structure"].passed
    assert results["automated-test-suite"].passed
    assert results["ci-test-command"].passed
