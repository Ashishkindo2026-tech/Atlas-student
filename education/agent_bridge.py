"""Bridge education retrieval and the student education profile into Atlas prompts."""
from .retrieval import build_context
from .student_profile import EducationProfile


def education_context(user: str) -> str:
    profile = EducationProfile()
    retrieved = build_context(user, limit=4)
    if retrieved.startswith("No indexed education material"):
        material = "No indexed CBSE/NCERT material matched this request. Do not claim textbook support."
    else:
        material = retrieved
    return f"{profile.context()}\n\nEDUCATION RETRIEVAL:\n{material}"
