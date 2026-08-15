"""Phase 32: diagnosis-first self-debugging helpers."""
from dataclasses import dataclass

@dataclass
class DebugDiagnosis:
    error: str
    cause: str
    proposed_fix: str
    tests: list[str]

class SelfDebugger:
    def diagnose(self, error: str, analyzer):
        result = analyzer(error)
        return DebugDiagnosis(error, result.get("cause", "unknown"), result.get("fix", ""), list(result.get("tests", [])))
