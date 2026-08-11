from memory.memory import recall
from brain.memory_router import MemoryRouter
from memory.history import add_message
from project.project_manager import list_projects
from tools.system_tools import get_time, get_date
from brain.core import build_context
from llm.ollama_client import Ollama_Client
from personality.personality import Personality
from goals.goal_manager import GoalManager
from user.knowledge import UserKnowledge


class AtlasAgent:
    def __init__(self):
        self.llm = Ollama_Client()
        self.memory_router = MemoryRouter()
        self.personality = Personality()
        self.goals = GoalManager()
        self.user_knowledge = UserKnowledge()
        self.pending_memory = None

    def process(self, user):
        text = user.strip()
        lower = text.lower()
        clean = lower.rstrip("?!.")

        if self.pending_memory:
            if clean in {"yes", "yes remember it", "remember it", "save it", "save", "okay", "ok"}:
                memory = self.pending_memory
                self.memory_router.save_memory(memory)
                self.pending_memory = None
                response = f"Okay. I'll remember that: {memory}"
                add_message("assistant", response)
                return response
            if clean in {"no", "don't", "dont", "no thanks", "don't remember it", "dont remember it"}:
                self.pending_memory = None
                response = "Okay. I won't save it."
                add_message("assistant", response)
                return response

        if clean in {
            "what have you learned about how i like you to respond",
            "what have you learned about my preferences",
            "show my personality preferences",
            "show adaptation",
        }:
            response = self.personality.explain()
            add_message("assistant", response)
            return response

        if clean in {"reset personality", "reset my preferences", "forget my response preferences"}:
            self.personality.reset()
            response = "Okay. I reset my learned response preferences."
            add_message("assistant", response)
            return response

        if clean in {"show goals", "what are my goals", "list goals"}:
            response = self.goals.summary()
            add_message("assistant", response)
            return response

        if clean.startswith("add goal ") or clean.startswith("my goal is "):
            goal = text.split(" ", 2)[2].strip() if clean.startswith("add goal ") else text[len("my goal is "):].strip()
            if self.goals.add_goal(goal):
                response = f"Got it. I've added this goal: {goal}"
            else:
                response = "That goal is already active or empty."
            add_message("assistant", response)
            return response

        if clean.startswith("complete goal "):
            goal = text[len("complete goal "):].strip()
            response = f"Goal completed: {goal}" if self.goals.complete_goal(goal) else f"I couldn't find an active goal named '{goal}'."
            add_message("assistant", response)
            return response

        if clean in {"show user profile", "what do you know about me"}:
            response = self.user_knowledge.summary()
            add_message("assistant", response)
            return response

        if clean == "reset user profile":
            self.user_knowledge.reset()
            response = "Okay. I reset the explicit user-knowledge profile."
            add_message("assistant", response)
            return response

        memory_result = self.memory_router.route(text)
        memory_type = memory_result["type"]

        if memory_type == "memory_request":
            self.pending_memory = memory_result["value"]
            response = f'I can remember this:\n"{self.pending_memory}"\n\nWould you like me to save it to long-term memory?'
            add_message("assistant", response)
            return response

        if memory_type == "show_memory":
            facts = self.memory_router.long_term.get_facts()
            important = self.memory_router.long_term.get_important_memories()
            parts = []
            if facts:
                parts.append("Facts:")
                parts.extend(f"- {k}: {v}" for k, v in facts.items())
            if important:
                parts.append("Important memories:")
                parts.extend(f"- {m}" for m in important)
            response = "\n".join(parts) if parts else "I don't have any long-term memories saved."
            add_message("assistant", response)
            return response

        if memory_type == "forget_all":
            self.memory_router.forget_all_memory()
            response = "Okay. I deleted the active long-term memories. Archived information is kept separately."
            add_message("assistant", response)
            return response

        if memory_type == "forget_request":
            query = memory_result["value"]
            deleted = self.memory_router.forget_memory(query)
            response = f"Okay. I forgot the memory about {query}." if deleted else f"I couldn't find a stored memory matching {query}."
            add_message("assistant", response)
            return response

        if clean == "what is my name":
            name = recall("name")
            response = f"Your name is {name}." if name else "I don't know your name yet."
            add_message("assistant", response)
            return response

        if clean in {"who created you"}:
            response = "I was created by Ashish."
            add_message("assistant", response)
            return response

        if clean in {"who are you", "what is your name"}:
            response = "I am Atlas."
            add_message("assistant", response)
            return response

        if "what time" in lower:
            response = get_time()
            add_message("assistant", response)
            return response

        if "what is today's date" in lower or "what is the date" in lower:
            response = get_date()
            add_message("assistant", response)
            return response

        if clean in {"list projects", "show projects"}:
            projects = list_projects()
            if not projects:
                response = "No projects found."
            else:
                parts = ["Projects:", ""]
                for name, data in projects.items():
                    parts.append(name)
                    for task in data.get("tasks", []):
                        parts.append(f"  - {task}")
                    parts.append("")
                response = "\n".join(parts)
            add_message("assistant", response)
            return response

        if clean in {"hello", "hi", "hey"}:
            name = recall("name")
            response = f"Hello {name}. How can I help you?" if name else "Hello. How can I help you?"
            add_message("assistant", response)
            return response

        response = self.ask_llm(text)
        add_message("assistant", response)
        return response

    def ask_llm(self, user):
        context = build_context(user)
        prompt = f"""
You are Atlas Student, a local-first personal AI for a student.

ATLAS PERSONALITY CORE:
{self.personality.get()}

{context['personality']}

USER NAME:
{context['name']}

APPROVED LONG-TERM MEMORIES:
{context['memories']}

ACTIVE GOALS:
{context['goals']}

EXPLICIT USER KNOWLEDGE:
{context['user_knowledge']}

AVAILABLE LOCAL TOOLS:
{context['tools']}

RECENT CONVERSATION:
{context['history']}

CURRENT USER MESSAGE:
{context['user_input']}

SYSTEM RULES:
1. Long-term memory requires explicit approval.
2. Conversation history is not automatically long-term memory.
3. Learned personality preferences are soft guidance and can change.
4. Prefer the current request when it conflicts with an older preference.
5. Never infer sensitive personal traits from writing style or behavior.
6. Never invent user facts, goals, memories, or achievements.
7. Atlas core values are immutable: honesty, privacy, safety, respect, user control, and no manipulation.
8. Do not claim to have used a tool unless the application actually used it.
9. For uncertain facts, say you don't know.
10. Answer directly and naturally for the current context.
"""
        return self.llm.ask(prompt)


_agent = AtlasAgent()


def process(user):
    return _agent.process(user)
