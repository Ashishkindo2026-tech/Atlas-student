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
from education.agent_bridge import education_context
from education.retrieval import retrieve
from education.study_planner import build_study_plan, format_plan
from student.progress_manager import ProgressManager
from learning.learning_signal_detector import detect as detect_learning_signal
from planning.exam_planner import ExamSubject, build_month_plan
import re


class AtlasAgent:
    def __init__(self):
        self.llm = None
        self.memory_router = MemoryRouter()
        self.personality = Personality()
        self.goals = GoalManager()
        self.user_knowledge = UserKnowledge()
        self.reasoning = ReasoningEngine()
        self.progress = ProgressManager()
        self.pending_memory = None

    def _reply(self, response):
        add_message("assistant", response)
        return response

    @staticmethod
    def _explicit_subject(text: str):
        subjects = ["physics", "chemistry", "mathematics", "math", "biology", "english", "science", "history", "geography", "computer science"]
        lower = text.lower()
        subject = next((s for s in subjects if re.search(rf"\b{re.escape(s)}\b", lower)), None)
        return "mathematics" if subject == "math" else subject

    def _learn_from_message(self, text: str):
        signal = detect_learning_signal(text)
        if signal is None:
            return None
        subject = self._explicit_subject(text)
        self.progress.record_learning_signal(signal.kind, signal.concept, signal.confidence, signal.evidence, subject)
        return signal

    @staticmethod
    def _exam_plan_request(user: str):
        """Recognize explicit multi-subject exam loads before any LLM call."""
        lower = re.sub(r"\s+", " ", user.lower()).strip()
        if "exam" not in lower:
            return None

        duration = re.search(r"\b(\d+)\s*(days?|weeks?|months?)\b", lower)
        if not duration:
            return None
        amount = int(duration.group(1))
        unit = duration.group(2)
        if unit.startswith("month"):
            days = amount * 30
        elif unit.startswith("week"):
            days = amount * 7
        else:
            days = amount

        aliases = {
            "physics": "Physics",
            "chemistry": "Chemistry",
            "mathematics": "Mathematics",
            "math": "Mathematics",
            "biology": "Biology",
            "english": "English",
        }
        matches = []
        for alias, display in aliases.items():
            # Accept "chapters in physics", "chapters of physics", and
            # common typos/connectors such as "abd" in natural messages.
            pattern = rf"\b(\d+)\s+chapters?\s+(?:in|of)\s+{re.escape(alias)}\b"
            for match in re.finditer(pattern, lower):
                matches.append((match.start(), ExamSubject(display, int(match.group(1)))))

        if len(matches) < 2:
            return None
        matches.sort(key=lambda item: item[0])
        # De-duplicate aliases while preserving the user's order.
        subjects = []
        seen = set()
        for _, subject in matches:
            if subject.name not in seen:
                subjects.append(subject)
                seen.add(subject.name)
        return days, subjects if len(subjects) >= 2 else None

    def process(self, user):
        text = user.strip()
        lower = text.lower()
        clean = lower.rstrip("?!.")
        if not text:
            return self._reply("Tell me what you'd like to work on.")

        self._learn_from_message(text)

        # Deterministic exam planning MUST run before generic greetings/LLM.
        # This prevents an explicit exam request from falling through to the
        # conversational model and returning an unrelated greeting.
        exam_request = self._exam_plan_request(text)
        if exam_request:
            days, subjects = exam_request
            return self._reply(build_month_plan(days, subjects))

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
        if clean in {"show progress", "show my progress", "learning progress", "what is my learning progress"}:
            return self._reply(self.progress.summary())
        if clean == "reset learning progress":
            self.progress.reset()
            return self._reply("Okay. I reset the learning-progress record.")

        if clean.startswith("study session "):
            parts = text[len("study session "):].strip().split()
            if len(parts) >= 2:
                try:
                    minutes = int(parts[1])
                    subject = parts[0]
                    topic = " ".join(parts[2:])
                    if self.progress.record_session(subject, minutes, topic):
                        return self._reply(f"Recorded {minutes} minutes of {subject} study.")
                except ValueError:
                    pass
            return self._reply("Use: study session <subject> <minutes> [topic]")

        if clean.startswith("set mastery "):
            raw = text[len("set mastery "):].strip().split("|")
            if len(raw) == 3:
                try:
                    ok = self.progress.set_mastery(raw[0], raw[1], int(raw[2].strip()))
                    return self._reply("Mastery updated." if ok else "Mastery must be between 0 and 100.")
                except ValueError:
                    pass
            return self._reply("Use: set mastery <subject> | <concept> | <0-100>")

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

    @staticmethod
    def _study_request(user: str):
        match = re.search(r"(?:have|got|only|just)\s+(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)", user.lower())
        if not match:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)", user.lower())
        if not match:
            return None
        amount = float(match.group(1))
        unit = match.group(2)
        minutes = int(amount * 60) if unit.startswith(("hour", "hr")) else int(amount)
        subjects = ["physics", "chemistry", "mathematics", "math", "biology", "english", "science", "history", "geography", "computer science"]
        subject = next((s for s in subjects if s in user.lower()), None)
        if subject == "math": subject = "mathematics"
        return subject, minutes

    def ask_llm(self, user):
        context = build_context(user)
        reasoning_plan = self.reasoning.plan(user, context)
        study_request = self._study_request(user)
        if reasoning_plan.missing:
            if reasoning_plan.intent == "study_planning" and "subject" in reasoning_plan.missing:
                return self._reply("I can make the plan, but I need one important detail first: what subject is the exam for?")

        if study_request:
            subject, minutes = study_request
            if subject and minutes > 0:
                retrieved = retrieve(subject, limit=12)
                plan = build_study_plan(subject.title(), minutes, retrieved, self.progress.data())
                return self._reply(format_plan(subject.title(), minutes, plan))

        if self.llm is None:
            self.llm = Ollama_Client()
        reasoning = self.reasoning.prompt_context(user, context)
        education = education_context(user)
        progress = self.progress.summary()
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
LEARNING PROGRESS:
{progress}
AVAILABLE LOCAL TOOLS:
{context['tools']}
RECENT CONVERSATION:
{context['history']}

CBSE/NCERT EDUCATION RETRIEVAL:
{education}

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
6. Never invent user facts, goals, memories, achievements, or learning progress.
7. Atlas core values are immutable: honesty, privacy, safety, respect, user control, and no manipulation.
8. Do not claim to have used a tool unless the application actually used it.
9. For uncertain facts, say you don't know.
10. Use the reasoning layer as a planning scaffold, then produce a direct, useful response.
11. If constraints are missing, ask for the missing information instead of inventing it.
12. For plans, verify that proposed actions fit the user's stated time and constraints.
13. A stored preference such as favorite_subject is not evidence of the subject of the current exam.
14. When education retrieval is present, use it as the primary source for NCERT/CBSE-specific questions and preserve page/source references when useful.
15. Never claim that content is from an NCERT/CBSE book when no matching indexed education source was retrieved.
16. Treat learning progress as evidence only when explicitly recorded; never manufacture mastery scores.
17. For explicit study-planning requests, use the deterministic study planner when indexed material is available rather than inventing chapters.
18. Learning signals are evidence only. Do not convert one message into a mastery percentage.
"""
        return self.llm.ask(prompt)


_agent = AtlasAgent()


def process(user):
    return _agent.process(user)
