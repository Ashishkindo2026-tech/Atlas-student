from memory.memory_manager import MemoryManager


class MemoryRouter:

    def __init__(self):

        self.long_term = MemoryManager()

    def route(self, user_input):

        text = user_input.strip()
        lower = text.lower()

        # ==================================================
        # SHOW MEMORY
        # ==================================================

        show_commands = [
            "show my memories",
            "show memories",
            "what do you remember",
            "what do you remember about me",
            "show my memory"
        ]

        if lower in show_commands:

            return {
                "type": "show_memory",
                "value": None
            }

        # ==================================================
        # FORGET ALL
        # ==================================================

        forget_all_commands = [
            "forget all my memories",
            "forget all memories",
            "delete all my memories",
            "delete all memories",
            "remove all my memories",
            "remove all memories"
        ]

        if lower in forget_all_commands:

            return {
                "type": "forget_all",
                "value": None
            }

        # ==================================================
        # FORGET SPECIFIC MEMORY
        # ==================================================

        forget_starts = [
            "forget ",
            "forget that ",
            "delete ",
            "delete that ",
            "remove ",
            "remove that "
        ]

        for prefix in forget_starts:

            if lower.startswith(prefix):

                memory_text = text[len(prefix):].strip()

                if memory_text:

                    return {
                        "type": "forget_request",
                        "value": memory_text
                    }

        # ==================================================
        # SAVE REQUEST
        # IMPORTANT:
        # NEVER SAVE AUTOMATICALLY
        # ==================================================

        remember_starts = [
            "remember that ",
            "please remember ",
            "don't forget that ",
            "do not forget that "
        ]

        for prefix in remember_starts:

            if lower.startswith(prefix):

                memory_text = text[len(prefix):].strip()

                if memory_text:

                    return {
                        "type": "save_request",
                        "value": memory_text
                    }

        # ==================================================
        # NORMAL CONVERSATION
        # ==================================================

        return {
            "type": "conversation",
            "value": text
        }

    # ==================================================
    # SAVE APPROVED MEMORY
    # ==================================================

    def save_memory(self, memory):

        self.long_term.add_important_memory(memory)

    # ==================================================
    # FORGET MEMORY
    # ==================================================

    def forget_memory(self, query):

        memories = self.long_term.get_important_memories()

        query_lower = query.lower()

        for memory in memories:

            if query_lower in memory.lower():

                return self.long_term.delete_important_memory(memory)

        return False

    # ==================================================
    # FORGET EVERYTHING
    # ==================================================

    def forget_all_memory(self):

        return self.long_term.delete_all_memory()