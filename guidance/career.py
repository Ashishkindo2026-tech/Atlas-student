"""Career/subject guidance from student evidence, not deterministic prescriptions."""
from __future__ import annotations
from typing import Any, Dict, List


PATHS = {
    "engineering": {"subjects": ["physics", "mathematics", "computer science"], "skills": ["problem solving", "mathematical reasoning"]},
    "medicine": {"subjects": ["biology", "chemistry"], "skills": ["careful reasoning", "scientific reading"]},
    "computer science": {"subjects": ["mathematics", "computer science", "physics"], "skills": ["logic", "programming", "problem solving"]},
    "design": {"subjects": ["art", "design", "computer science"], "skills": ["visual thinking", "communication", "iteration"]},
    "research": {"subjects": ["mathematics", "physics", "chemistry", "biology"], "skills": ["analysis", "experimentation", "writing"]},
}


class GuidanceEngine:
    def recommend(self, strengths: Dict[str, float], interests: List[str] | None = None, limit: int = 5) -> List[Dict[str, Any]]:
        interests = [x.casefold() for x in (interests or [])]
        results = []
        for name, path in PATHS.items():
            score = sum(float(strengths.get(s, 0)) for s in path["subjects"]) / max(1, len(path["subjects"]))
            score += sum(10 for i in interests if i in name or name in i)
            results.append({"path": name, "score": round(score, 2), "why": {"subjects": path["subjects"], "skills": path["skills"]}})
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    def explain(self, path: str) -> str:
        item = PATHS.get(path.casefold())
        if not item: return "I don't have a guidance profile for that path yet."
        return f"{path.title()} can connect with: {', '.join(item['subjects'])}. Useful skills: {', '.join(item['skills'])}. This is guidance, not a fixed decision."
