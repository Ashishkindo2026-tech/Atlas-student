"""Phase 18: profile-aware opportunity ranking."""
from dataclasses import dataclass

@dataclass
class Opportunity:
    title: str
    category: str
    age_appropriate: bool = True
    relevance: float = 0.0

class OpportunityEngine:
    def rank(self, opportunities, interests: set[str]):
        ranked = []
        for item in opportunities:
            tags = set(getattr(item, "tags", set()))
            score = len(tags & interests)
            if getattr(item, "age_appropriate", True):
                score += 1
            item.relevance = score
            ranked.append(item)
        return sorted(ranked, key=lambda x: x.relevance, reverse=True)
