"""Atlas Student quality gates for the A-J roadmap.

The gate is deliberately evidence-driven: a phase cannot be marked complete
unless its required checks are present and passing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PHASES = {
    "A": ("Foundation", ("architecture", "code_quality", "dependencies", "configuration")),
    "B": ("Intelligence", ("llm", "reasoning", "context", "memory", "tool_use")),
    "C": ("Student", ("tutoring", "notes", "revision", "questions", "study_planning")),
    "D": ("Interaction", ("voice", "wake_word", "gui", "personality", "multimodal")),
    "E": ("Performance", ("ollama_optimization", "quantization", "cpu", "ram", "benchmarking", "low_end_mode")),
    "F": ("Reliability", ("automated_tests", "error_recovery", "logging", "monitoring", "regression")),
    "G": ("Privacy", ("local_first", "secure_memory", "permissions", "data_controls")),
    "H": ("Distribution", ("installer", "setup", "hardware_detection", "model_selection")),
    "I": ("Benchmark", ("atlas_suite", "subsystem_tests", "hardware_comparison", "published_results")),
    "J": ("10/10", ("audit", "fix", "retest", "zero_major_weaknesses")),
}


@dataclass(frozen=True)
class GateResult:
    phase: str
    score: float
    passed: bool
    missing: tuple[str, ...]


def evaluate_phase(phase: str, evidence: Iterable[str]) -> GateResult:
    key = phase.upper()
    if key not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    required = set(PHASES[key][1])
    present = set(evidence)
    missing = tuple(sorted(required - present))
    score = round((len(required) - len(missing)) / len(required) * 10, 1)
    return GateResult(key, score, not missing, missing)


def all_phases_passed(evidence_by_phase: dict[str, Iterable[str]]) -> bool:
    return all(evaluate_phase(k, v).passed for k, v in PHASES.items() if k in evidence_by_phase)
