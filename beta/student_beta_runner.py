"""Offline Student Beta v0.1 scenario runner.

Runs realistic student workflows against Atlas components without requiring
internet access or real textbook PDFs. This is a pre-release harness, not a
claim of external student validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from brain.agent import AtlasAgent


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    details: str = ""


@dataclass
class BetaReport:
    results: List[ScenarioResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def success(self) -> bool:
        return self.total > 0 and self.passed == self.total

    def text(self) -> str:
        lines = [f"Atlas Student Beta v0.1: {self.passed}/{self.total} scenarios passed"]
        for result in self.results:
            state = "PASS" if result.passed else "FAIL"
            suffix = f" — {result.details}" if result.details else ""
            lines.append(f"[{state}] {result.name}{suffix}")
        return "\n".join(lines)


def _scenario(name: str, fn: Callable[[], None]) -> ScenarioResult:
    try:
        fn()
        return ScenarioResult(name, True)
    except AssertionError as exc:
        return ScenarioResult(name, False, str(exc) or "assertion failed")
    except Exception as exc:  # keep the harness reportable even if a scenario crashes
        return ScenarioResult(name, False, f"{type(exc).__name__}: {exc}")


def run_beta(agent: AtlasAgent | None = None) -> BetaReport:
    """Run core student workflows in a deterministic offline environment."""
    agent = agent or AtlasAgent()
    report = BetaReport()

    def empty_request():
        assert agent.process("") == "Tell me what you'd like to work on."

    def missing_subject():
        response = agent.process("I have 30 minutes to study")
        assert "what subject" in response.lower()

    def explicit_subject_without_material():
        response = agent.process("I have 30 minutes for Physics")
        assert response.strip()
        assert "indexed ncert material" in response.lower()

    def memory_confirmation():
        response = agent.process("remember that I study best in the evening")
        assert "would you like me to save" in response.lower()

    def evidence_signal():
        response = agent.process("I still don't understand Newton's third law")
        assert response.strip()

    def direct_learning_question():
        response = agent.process("Explain Newton's third law simply.")
        assert response.strip()

    report.results.extend([
        _scenario("Empty request is handled safely", empty_request),
        _scenario("Missing subject is never guessed", missing_subject),
        _scenario("Explicit subject stays source-grounded", explicit_subject_without_material),
        _scenario("Long-term memory requires confirmation", memory_confirmation),
        _scenario("Learning difficulty is accepted as evidence", evidence_signal),
        _scenario("Direct learning question gets a response", direct_learning_question),
    ])
    return report


if __name__ == "__main__":
    report = run_beta()
    print(report.text())
    raise SystemExit(0 if report.success else 1)
