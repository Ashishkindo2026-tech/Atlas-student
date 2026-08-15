"""Phase 36: evidence-based strategy memory."""
from dataclasses import dataclass

@dataclass
class StrategyEvidence:
    strategy: str
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    score: float = 0.0

class StrategyMemory:
    def __init__(self): self.data={}
    def record(self, strategy, success, score=0.0):
        s=self.data.setdefault(strategy, StrategyEvidence(strategy)); s.attempts+=1; s.successes+=int(success); s.failures+=int(not success); s.score+=score
    def best(self):
        return max(self.data.values(), key=lambda s:(s.successes/max(1,s.attempts),s.score/max(1,s.attempts)), default=None)
