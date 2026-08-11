"""Bridge education retrieval into Atlas Agent prompts without changing the LLM client."""
from .retrieval import build_context


def education_context(user: str) -> str:
    context = build_context(user, limit=4)
    if context.startswith("No indexed education material"):
        return "No indexed CBSE/NCERT material matched this request. Do not claim textbook support."
    return context
