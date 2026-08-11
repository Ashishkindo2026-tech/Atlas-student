from memory.memory import recall
from brain.memory_router import MemoryRouter
from memory.history import add_message
from project.project_manager import list_projects
from tools.system_tools import get_time, get_date
from brain.core import build_context
from llm.ollama_client import Ollama_Client


class AtlasAgent:

    def __init__(self):

        self.llm = Ollama_Client()

        self.memory_router = MemoryRouter()

        # Memory waiting for user approval
        self.pending_memory = None

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, user):

        user_lower = user.lower().strip()

        # ==================================================
        # SAVE USER MESSAGE
        # ==================================================

        add_message("user", user)

        # ==================================================
        # PENDING MEMORY APPROVAL
        # ==================================================

        if self.pending_memory:

            if user_lower in [
                "yes",
                "yes remember it",
                "remember it",
                "save it",
                "save",
                "okay",
                "ok"
            ]:

                memory = self.pending_memory

                self.memory_router.save_memory(memory)

                self.pending_memory = None

                response = (
                    f"Okay. I'll remember that: {memory}"
                )

                add_message("assistant", response)

                return response

            if user_lower in [
                "no",
                "don't",
                "dont",
                "no thanks",
                "don't remember it",
                "dont remember it"
            ]:

                self.pending_memory = None

                response = "Okay. I won't save it."

                add_message("assistant", response)

                return response

        # ==================================================
        # MEMORY ROUTER
        # ==================================================

        memory_result = self.memory_router.route(user)

        memory_type = memory_result["type"]

        print(f"[DEBUG] Memory type: {memory_type}")

        # ==================================================
        # SAVE REQUEST
        # ==================================================

        if memory_type == "save_request":

            self.pending_memory = memory_result["value"]

            response = (
                "I can remember this:\n"
                f"\"{self.pending_memory}\"\n\n"
                "Would you like me to save it to long-term memory?"
            )

            add_message("assistant", response)

            return response

        # ==================================================
        # SHOW MEMORY
        # ==================================================

        if memory_type == "show_memory":

            facts = self.memory_router.long_term.get_facts()

            important = (
                self.memory_router
                .long_term
                .get_important_memories()
            )

            if not facts and not important:

                response = "I don't have any long-term memories saved."

            else:

                parts = []

                if facts:

                    parts.append("Facts:")

                    for key, value in facts.items():

                        parts.append(
                            f"- {key}: {value}"
                        )

                if important:

                    parts.append("\nImportant memories:")

                    for memory in important:

                        parts.append(
                            f"- {memory}"
                        )

                response = "\n".join(parts)

            add_message("assistant", response)

            return response

        # ==================================================
        # FORGET ALL
        # ==================================================

        if memory_type == "forget_all":

            self.memory_router.forget_all_memory()

            response = (
                "Okay. I deleted all of your long-term memories."
            )

            add_message("assistant", response)

            return response

        # ==================================================
        # FORGET REQUEST
        # ==================================================

        if memory_type == "forget_request":

            query = memory_result["value"]

            deleted = self.memory_router.forget_memory(query)

            if deleted:

                response = (
                    f"Okay. I forgot the memory about {query}."
                )

            else:

                response = (
                    f"I couldn't find a stored memory "
                    f"matching {query}."
                )

            add_message("assistant", response)

            return response

        # ==================================================
        # NAME
        # ==================================================

        if user_lower.rstrip("?!.") == "what is my name":

            name = recall("name")

            if name:

                response = f"Your name is {name}."

            else:

                response = "I don't know your name yet."

            add_message("assistant", response)

            return response

        # ==================================================
        # FAVORITE SUBJECT
        # ==================================================

        if user_lower.rstrip("?!.") in [
            "what is my favorite subject",
            "what's my favorite subject",
            "what is my favourite subject",
            "what's my favourite subject"
        ]:

            subject = recall("favorite_subject")

            if subject:

                response = (
                    f"Your favorite subject is {subject}."
                )

            else:

                response = (
                    "I don't know your favorite subject yet."
                )

            add_message("assistant", response)

            return response

        # ==================================================
        # CREATOR
        # ==================================================

        if user_lower.rstrip("?!.") == "who created you":

            response = "I was created by Ashish."

            add_message("assistant", response)

            return response

        # ==================================================
        # IDENTITY
        # ==================================================

        if user_lower.rstrip("?!.") in [
            "who are you",
            "what is your name"
        ]:

            response = "I am Atlas."

            add_message("assistant", response)

            return response

        # ==================================================
        # TIME
        # ==================================================

        if "what time" in user_lower:

            response = get_time()

            add_message("assistant", response)

            return response

        # ==================================================
        # DATE
        # ==================================================

        if (
            "what is today's date" in user_lower
            or "what is the date" in user_lower
        ):

            response = get_date()

            add_message("assistant", response)

            return response

        # ==================================================
        # PROJECTS
        # ==================================================

        if user_lower in [
            "list projects",
            "show projects"
        ]:

            projects = list_projects()

            if not projects:

                response = "No projects found."

            else:

                response = "Projects:\n\n"

                for name, data in projects.items():

                    response += f"{name}\n"

                    for task in data["tasks"]:

                        response += f"  - {task}\n"

                    response += "\n"

            add_message("assistant", response)

            return response

        # ==================================================
        # GREETINGS
        # ==================================================

        if user_lower.rstrip("?!.") in [
            "hello",
            "hi",
            "hey"
        ]:

            name = recall("name")

            if name:

                response = (
                    f"Hello {name}. How can I help you?"
                )

            else:

                response = "Hello. How can I help you?"

            add_message("assistant", response)

            return response

        # ==================================================
        # LLM FALLBACK
        # ==================================================

        response = self.ask_llm(user)

        add_message("assistant", response)

        return response

    # ==================================================
    # LLM
    # ==================================================

    def ask_llm(self, user):

        context = build_context(user)

        prompt = f"""
You are Atlas, a local AI assistant.

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

3. Do not treat something merely appearing in conversation
   history as a saved memory.

4. Use a memory only when it is explicitly present in
   APPROVED LONG-TERM MEMORIES.

5. Never invent information about the user's projects,
   interests, school, family, or life.

6. Do not combine unrelated memories.

7. If approved memories do not contain enough information,
   say that you don't know.

8. Never claim to remember something unless the user
   explicitly approved saving it.

9. Answer the current question directly.

Keep the answer concise and appropriate for a student.
"""

        return self.llm.ask(prompt)


# ==================================================
# COMPATIBILITY FUNCTION
# ==================================================

_agent = AtlasAgent()


def process(user):

    return _agent.process(user)