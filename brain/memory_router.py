from memory.memory_manager import MemoryManager


class MemoryRouter:
    def __init__(self):
        self.long_term = MemoryManager()

    def route(self, user_input):
        text = user_input.strip()
        lower = text.lower()

        # Explicit request to remember something.
        prefixes = [
            "remember that ",
            "please remember ",
            "don't forget that ",
            "do not forget that ",
        ]
        for prefix in prefixes:
            if lower.startswith(prefix):
                memory_text = text[len(prefix):].strip()
                if memory_text:
                    return {"type": "memory_request", "value": memory_text}

        # Explicit request to forget something.
        prefixes = [
            "forget ",
            "please forget ",
            "delete ",
            "remove from memory ",
        ]
        for prefix in prefixes:
            if lower.startswith(prefix):
                query = text[len(prefix):].strip()
                if query:
                    return {"type": "forget_request", "value": query}

        if lower in ["show memory", "show my memory", "what do you remember"]:
            return {"type": "show_memory", "value": None}

        if lower in ["forget everything", "forget all", "delete all memories"]:
            return {"type": "forget_all", "value": None}

        return {"type": "conversation", "value": None}

    def save_memory(self, memory_text):
        self.long_term.add_important_memory(memory_text)

    def forget_memory(self, query):
        memories = self.long_term.get_important_memories()
        query_words = query.lower().split()

        for memory in memories:
            memory_lower = memory.lower()
            if all(word in memory_lower for word in query_words):
                self.long_term.delete_important_memory(memory)
                return True

        return False

    def forget_all_memory(self):
        for memory in list(self.long_term.get_important_memories()):
            self.long_term.delete_important_memory(memory)
