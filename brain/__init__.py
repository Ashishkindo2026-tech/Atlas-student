def detect_intent(user):

    text = user.lower()

    if any(word in text for word in ["project", "task"]):
        return "project"

    if any(word in text for word in ["time", "date"]):
        return "system"

    if any(word in text for word in ["remember", "name"]):
        return "memory"

    if any(word in text for word in ["open"]):
        return "tool"

    return "llm"