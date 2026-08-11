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
from brain.reasoning_engine import ReasoningEngine


class AtlasAgent:
    def __init__(self):
        self.llm = Ollama_Client()
        self.memory_router = MemoryRouter()
        self.personality = Personality()
        self.goals = GoalManager()
        self.user_knowledge = UserKnowledge()
        self.reasoning = ReasoningEngine()
        self.pending_memory = None

    def _reply(self, response):
        add_message("assistant", response)
        return response

    def process(self, user):
        text = user.strip()
        lower = text.lower()
        clean = lower.rstrip("?!.")
        if not text:
            return self._reply("Tell me what you'd like to work on.")

        if self.pending_memory:
            if clean in {"yes", "yes remember it", "remember it", "save it", "save", "okay", "ok"}:
                memory = self.pending_memory
                self.memory_router.save_memory(memory)
                self.pending_memory = None
                return self._reply(f"Okay. I'll remember that: {memory}")
            if clean in {"no", "don't", "dont", "no thanks", "don't remember it", "dont remember it"}:
                self.pending_memory = None
                return self._reply("Okay. I won't save it.")

        if clean in {"what have you learned about how i like you to respond", "what have you learned about my preferences", "show my personality preferences", "show adaptation"}:
            return self._reply(self.personality.explain())
        if clean in {"reset personality", "reset my preferences", "forget my response preferences"}:
            self.personality.reset()
            return self._reply("Okay. I reset my learned response preferences.")
        if clean in {"show goals", "what are my goals", "list goals"}:
            return self._reply(self.goals.summary())

        if clean.startswith("add goal ") or clean.startswith("my goal is "):
            prefix = "add goal " if clean.startswith("add goal ") else "my goal is "
            goal = text[len(prefix):].strip()
            return self._reply(f"Got it. I've added this goal: {goal}" if self.goals.add_goal(goal) else "That goal is already active or empty.")

        if clean.startswith("progress goal "):
            remainder = text[len("progress goal "):].strip()
            if "%" in remainder:
                before = remainder.rsplit("%", 1)[0]
                parts = before.rsplit(" ", 1)
                if len(parts) == 2:
                    try:
                        goal, progress = parts[0], int(parts[1])
                        return self._reply("Goal progress updated." if self.goals.update_progress(goal, progress) else "I couldn't find that active goal.")
                    except ValueError:
                        pass

        if clean.startswith("complete goal "):
            goal = text[len("complete goal "):].strip()
            return self._reply(f"Goal completed: {goal}" if self.goals.complete_goal(goal) else f"I couldn't find an active goal named '{goal}'.")
        if clean in {"show user profile", "what do you know about me"}:
            return self._reply(self.user_knowledge.summary())
        if clean == "reset user profile":
            self.user_knowledge.reset()
            return self._reply("Okay. I reset the explicit user-knowledge profile.")

        memory_result = self.memory_router.route(text)
        memory_type = memory_result["type"]
        if memory_type == "memory_request":
            self.pending_memory = memory_result["value"]
            return self._reply(f'I can remember this:\n"{self.pending_memory}"\n\nWould you like me to save it to long-term memory?')
        if memory_type == "show_memory":
            facts = self.memory_router.long_term.get_facts()
            important = self.memory_router.long_term.get_important_memories()
            parts = (["Facts:"] + [f"- {k}: {v}" for k, v in facts.items()]) if facts else []
            if important:
                parts += ["Important memories:"] + [f"- {m}" for m in important]
            return self._reply("\n".join(parts) if parts else "I don't have any long-term memories saved.")
        if memory_type == "show_archive":
            archive = self.memory_router.get_archive()
            items = archive.get("items", []) if isinstance(archive, dict) else archive
            if not items:
                return self._reply("The memory archive is empty.")
            return self._reply("Archived memories:\n" + "\n".join(f"- {item.get('content', item.get('text', item))}" if isinstance(item, dict) else f"- {item}" for item in items[-20:]))
        if memory_type == "forget_all":
            self.memory_router.forget_all_memory()
            return self._reply("Okay. I removed the active long-term memories. Archived information is kept separately.")
        if memory_type == "forget_request":
            query = memory_result["value"]
            deleted = self.memory_router.forget_memory(query)
            return self._reply(f"Okay. I archived the memory about {query}." if deleted else f"I couldn't find a stored memory matching {query}.")

        if clean == "what is my name":
            name = recall("name")
            return self._reply(f"Your name is {name}." if name else "I don't know your name yet.")
        if clean == "who created you":
            return self._reply("I was created by Ashish.")
        if clean in {"who are you", "what is your name"}:
            return self._reply("I am Atlas.")
        if "what time" in lower:
            return self._reply(get_time())
        if "what is today's date" in lower or "what is the date" in lower:
            return self._reply(get_date())
        if clean in {"list projects", "show projects"}:
            projects = list_projects()
            if not projects:
                return self._reply("No projects found.")
            parts = ["Projects:", ""]
            for name, data in projects.items():
                parts.append(name)
                parts.extend(f"  - {task}" for task in data.get("tasks", []))
                parts.append("")
            return self._reply("\n".join(parts))
        if clean in {"hello", "hi", "hey"}:
            name = recall("name")
            return self._reply(f"Hello {name}. How can I help you?" if name else "Hello. How can I help you?")

        return self._reply(self.ask_llm(text))

    def ask_llm(self, user):
        context = build_context(user)
        reasoning_plan = self.reasoning.plan(user, context)
        if reasoning_plan.missing:
            if reasoning_plan.intent == "study_planning" and "subject" in reasoning_plan.missing:
                return self._reply("I can make the 2-hour plan, but I need one important detail first: what subject is the exam for?")

        reasoning = self.reasoning.prompt_context(user, context)
        prompt = f"""You are Atlas Student, a local-first personal AI for a student.

ATLAS PERSONALITY CORE:
{self.personality.get()}

{context['personality']}
USER NAME: {context['name']}
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

REASONING LAYER:
{reasoning}

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
10. Use the reasoning layer as a planning scaffold, then produce a direct, useful response.
11. If constraints are missing, ask for the missing information instead of inventing it.
12. For plans, verify that proposed actions fit the user's stated time and constraints.
13. A stored preference such as favorite_subject is not evidence of the subject of the current exam.
"""
        return self.llm.ask(prompt)


_agent = AtlasAgent()


def process(user):
    return _agent.process(user)
