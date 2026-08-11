from memory.memory import recall
from memory.history import get_recent_messages
from brain.memory_relevance import MemoryRelevance
from goals.goal_manager import GoalManager
from user.knowledge import UserKnowledge
from personality.personality import Personality
from tools.tool_manager import ToolManager

memory_relevance = MemoryRelevance()
goal_manager = GoalManager()
user_knowledge = UserKnowledge()
personality = Personality()
tool_manager = ToolManager()


def build_context(user_input):
    """Build the complete local context before Atlas reasons."""
    return {
        "name": recall("name"),
        "history": get_recent_messages(12),
        "memories": memory_relevance.find(user_input),
        "goals": goal_manager.summary(),
        "user_knowledge": user_knowledge.summary(),
        "personality": personality.prompt_block(user_input),
        "tools": tool_manager.describe(),
        "user_input": user_input,
    }
