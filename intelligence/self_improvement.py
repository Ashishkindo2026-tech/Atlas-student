"""Phase 20: privacy-preserving strategy improvement."""
from dataclasses import dataclass, field

@dataclass
class StrategyStats:
    attempts: int = 0
    successes: int = 0
    total_score: float = 0.0
    abandonment_count: int = 0

class SelfImprovement:
    def __init__(self):
        self.stats: dict[str, StrategyStats] = {}

    def record(self, strategy: str, success: bool, score: float = 0.0, abandoned: bool = False):
        s = self.stats.setdefault(strategy, StrategyStats())
        s.attempts += 1
        s.successes += int(success)
        s.total_score += score
        s.abandonment_count += int(abandoned)

    def best_strategy(self):
        if not self.stats:
            return None
        return max(self.stats, key=lambda k: (self.stats[k].successes / max(1, self.stats[k].attempts), self.stats[k].total_score / max(1, self.stats[k].attempts)))
