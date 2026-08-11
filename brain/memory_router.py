from memory.memory_manager import MemoryManager
from memory.archive_manager import ArchiveManager


class MemoryRouter:
    def __init__(self):
        self.long_term = MemoryManager()
        self.archive = ArchiveManager()

    def route(self, user_input):
        text = user_input.strip()
        lower = text.lower()

        for prefix in ["remember that ", "please remember ", "don't forget that ", "do not forget that ", "remember "]:
            if lower.startswith(prefix):
                value = text[len(prefix):].strip()
                if value:
                    return {"type": "memory_request", "value": value}

        for prefix in ["forget ", "please forget ", "delete ", "remove from memory "]:
            if lower.startswith(prefix):
                value = text[len(prefix):].strip()
                if value:
                    return {"type": "forget_request", "value": value}

        if lower in {"show memory", "show my memory", "what do you remember"}:
            return {"type": "show_memory", "value": None}
        if lower in {"forget everything", "forget all", "delete all memories"}:
            return {"type": "forget_all", "value": None}
        if lower in {"show archive", "show archived memories", "what is archived"}:
            return {"type": "show_archive", "value": None}
        return {"type": "conversation", "value": None}

    def save_memory(self, memory_text):
        return self.long_term.add_important_memory(memory_text)

    def forget_memory(self, query):
        query_words = query.lower().split()
        for memory in list(self.long_term.get_important_memories()):
            if all(word in memory.lower() for word in query_words):
                self.archive.archive("important_memory", memory, "user_requested_forget")
                self.long_term.delete_important_memory(memory)
                return True
        return False

    def forget_all_memory(self):
        for memory in list(self.long_term.get_important_memories()):
            self.archive.archive("important_memory", memory, "user_requested_forget_all")
            self.long_term.delete_important_memory(memory)

    def get_archive(self):
        return self.archive.get_all()
