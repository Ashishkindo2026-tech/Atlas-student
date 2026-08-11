from memory.memory import recall
from memory.history import get_recent_messages
from brain.memory_relevance import MemoryRelevance


memory_relevance = MemoryRelevance()


def build_context(user_input):
    """
    Builds all context before Atlas thinks.
    """

    context = {}

    # -------------------------
    # User Profile
    # -------------------------

    context["name"] = recall("name")

    # -------------------------
    # Recent Conversation
    # -------------------------

    context["history"] = get_recent_messages(10)

    # -------------------------
    # Relevant Memories
    # -------------------------

    context["memories"] = memory_relevance.find(
        user_input
    )

    # -------------------------
    # Current User Input
    # -------------------------

    context["user_input"] = user_input

    return context