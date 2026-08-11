from memory.memory import recall
from brain.memory_router import MemoryRouter
from memory.history import add_message
from project.project_manager import list_projects
from tools.system_tools import get_time, get_date
from brain.core import build_context
from llm.ollama_client import Ollama_Client
from personality.personality import Personality


class AtlasAgent:
    def __init__(self):
        self.llm = Ollama_Client()
        self.memory_router = MemoryRouter()
        self.personality = Personality()
        self.pending_memory = None

    def process(self, user):
        user_lower = user.lower().strip()

        # Memory approval must be handled before routing the new message.
        if self.pending_memory:
            if user_lower in ["yes", "yes remember it", "remember it", "save it", "save", "okay", "ok"]:
                memory = self.pending_memory
                self.memory_router.save_memory(memory)
                self.pending_memory = None
                response = f"Okay. I'll remember that: {memory}"
                add_message("assistant", response)
                return response

            if user_lower in ["no", "don't", "dont", "no thanks", "don't remember it", "dont remember it"]:
                self.pending_memory = None
                response = "Okay. I won't save it."
                add_message("assistant", response)
                return response

        # Personality controls are separate from factual long-term memory.
        if user_lower in [
            "what have you learned about how i like you to respond",
            "what have you learned about my preferences",
            "show my personality preferences",
            "show adaptation",
        ]:
            response = self.personality.explain()
            add_message("assistant", response)
            return response

        if user_lower in ["reset personality", "reset my preferences", "forget my response preferences"]:
            self.personality.reset()
            response = "Okay. I reset my learned response preferences."
            add_message("assistant", response)
            return response

        memory_result = self.memory_router.route(user)
        memory_type = memory_result["type"]
        print(f"[DEBUG] Memory type: {memory_type}")

        if memory_type == "memory_request":
            self.pending_memory = memory_result["value"]
            response = (
                "I can remember this:\n"
                f"\"{self.pending_memory}\"\n\n"
                "Would you like me to save it to long-term memory?"
            )
            add_message("assistant", response)
            return response

        if memory_type == "show_memory":
            facts = self.memory_router.long_term.get_facts()
            important = self.memory_router.long_term.get_important_memories()
            if not facts and not important:
                response = "I don't have any long-term memories saved."
            else:
                parts = []
                if facts:
                    parts.append("Facts:")
                    for key, value in facts.items():
                        parts.append(f"- {key}: {value}")
                if important:
                    parts.append("\nImportant memories:")
                    for memory in important:
                        parts.append(f"- {memory}")
                response = "\n".join(parts)
            add_message("assistant", response)
            return response

        if memory_type == "forget_all":
            self.memory_router.forget_all_memory()
            response = "Okay. I deleted all of your long-term memories."
            add_message("assistant", response)
            return response

        if memory_type == "forget_request":
            query = memory_result["value"]
            deleted = self.memory_router.forget_memory(query)
            response = (
                f"Okay. I forgot the memory about {query}."
                if deleted
                else f"I couldn't find a stored memory matching {query}."
            )
            add_message("assistant", response)
            return response

        if user_lower.rstrip("?!.") == "what is my name":
            name = recall("name")
            response = f"Your name is {name}." if name else "I don't know your name yet."
            add_message("assistant", response)
            return response

        if user_lower.rstrip("?!.") in [
            "what is my favorite subject",
            "what's my favorite subject",
            "what is my favourite subject",
            "what's my favourite subject",
        ]:
            subject = recall("favorite_subject")
            response = f"Your favorite subject is {subject}." if subject else "I don't know your favorite subject yet."
            add_message("assistant", response)
            return response

        if user_lower.rstrip("?!.") == "who created you":
            response = "I was created by Ashish."
            add_message("assistant", response)
            return response

        if user_lower.rstrip("?!.") in ["who are you", "what is your name"]:
            response = "I am Atlas."
            add_message("assistant", response)
            return response

        if "what time" in user_lower:
            response = get_time()
            add_message("assistant", response)
            return response

        if "what is today's date" in user_lower or "what is the date" in user_lower:
            response = get_date()
            add_message("assistant", response)
            return response

        if user_lower in ["list projects", "show projects"]:
            projects = list_projects()
            if not projects:
                response = "No projects found."
            else:
                parts = ["Projects:", ""]
                for name, data in projects.items():
                    parts.append(name)
                    for task in data["tasks"]:
                        parts.append(f"  - {task}")
                    parts.append("")
                response = "\n".join(parts)
            add_message("assistant", response)
            return response

        if user_lower.rstrip("?!.") in ["hello", "hi", "hey"]:
            name = recall("name")
            response = f"Hello {name}. How can I help you?" if name else "Hello. How can I help you?"
            add_message("assistant", response)
            return response

        response = self.ask_llm(user)
        add_message("assistant", response)
        return response

    def ask_llm(self, user):
        context = build_context(user)
        personality = self.personality.get()
        adaptation = self.personality.prompt_block(user)

        prompt = f"""
You are Atlas, a local AI assistant.

PERSONALITY CORE:
{personality}

{adaptation}

USER PROFILE:
{context["name"]}

APPROVED LONG-TERM MEMORIES:
{context["memories"]}

RECENT CONVERSATION:
{context["history"]}

CURRENT USER MESSAGE:
{context["user_input"]}

MEMORY RULES:
1. Only approved long-term memories are memory.
2. Conversation history is NOT long-term memory.
3. Do not treat something merely appearing in conversation history as a saved memory.
4. Use a memory only when it is explicitly present in APPROVED LONG-TERM MEMORIES.
5. Never invent information about the user's projects, interests, school, family, or life.
6. Do not combine unrelated memories.
7. If approved memories do not contain enough information, say that you don't know.
8. Never claim to remember something unless the user explicitly approved saving it.

PERSONALITY RULES:
1. Adapt tone, verbosity, language, humor, explanation depth, examples, and step-by-step style when reliable preferences exist.
2. Treat learned preferences as soft guidance, not permanent facts.
3. Prefer the current request when it conflicts with an older preference.
4. Do not infer sensitive traits, emotions, health, beliefs, identity, or other private characteristics from writing style.
5. Never change Atlas's core values: honesty, privacy, safety, respect, user control, and no manipulation.
6. Do not claim to know why a preference exists unless the user explicitly told you.

Answer the current question directly and naturally.
"""
        return self.llm.ask(prompt)


_agent = AtlasAgent()


def process(user):
    return _agent.process(user)
