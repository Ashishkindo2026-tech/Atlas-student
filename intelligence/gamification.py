"""Phase 15: learning-focused gamification."""
from dataclasses import dataclass, field

@dataclass
class GameProfile:
    xp: int = 0
    level: int = 1
    streak_days: int = 0
    achievements: set[str] = field(default_factory=set)

    def award_xp(self, amount: int):
        self.xp = max(0, self.xp + amount)
        self.level = max(1, self.xp // 100 + 1)
