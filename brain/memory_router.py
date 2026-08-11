from memory.memory import remember
from memory.memory_manager import MemoryManager


class MemoryRouter:

    def __init__(self):
        self.long_term = MemoryManager()

    def route(self, user_input):

        text = user_input.strip()
        lower = text.lower()

        # ==========================================
        # REMEMBER REQUEST
        # ==========================================

        prefixes = [
            "remember that ",
            "please remember ",
            "don't forget that ",
            "do not forget that "
        ]

        for prefix in prefixes:

            if lower.startswith(prefix):

                memory_text = text[len(prefix):].strip()

                if memory_text:

                    return {
                        "type": "memory_request",
                        "value": memory_text
                    }

        # ==========================================
        # FORGET REQUEST
        # ==========================================

        prefixes = [
            "forget ",
            "please forget ",
            "delete ",
            "remove from memory "
        ]

        for prefix in prefixes:

            if lower.startswith(prefix):

                query = text[len(prefix):].strip()

                if query:

                    return {
                        "type": "forget_request",
                        "value": query
                    }

        # ==========================================
        # NORMAL CONVERSATION
        # ==========================================

        return {
            "type": "conversation",
            "value": None
        }

    # ==========================================
    # SAVE MEMORY AFTER USER APPROVES
    # ==========================================

    def save_memory(self, memory_text):

        self.long_term.add_important_memory(memory_text)

    # ==========================================
    # FORGET MEMORY
    # ==========================================

    def forget_memory(self, query):

        memories = self.long_term.get_important_memories()

        query_words = query.lower().split()

        for memory in memories:

            memory_lower = memory.lower()

            if all(word in memory_lower for word in query_words):

                self.long_term.delete_important_memory(memory)

                return True

        return False