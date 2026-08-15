from memory.memory_manager import MemoryManager
from memory.archive_manager import ArchiveManager


class MemoryRouter:
    """Routes memory commands and exposes the unified memory API."""

    def __init__(self):
        self.long_term = MemoryManager()
        self.archive = ArchiveManager(self.long_term)

    def route(self, user_input):
        text = user_input.strip()
        lower = text.lower().rstrip("?!.")

        if lower in {"forget everything", "forget all", "delete all memories"}:
            return {"type": "forget_all", "value": None}
        if (
            lower in {"show memory", "show my memory", "what do you remember"}
            or lower.startswith("what do you remember about ")
            or lower.startswith("what do you remember of ")
            or lower.startswith("what do you know about ")
        ):
            return {"type": "show_memory", "value": None}
        if lower in {"show archive", "show archived memories", "what is archived"}:
            return {"type": "show_archive", "value": None}

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

        return {"type": "conversation", "value": None}

    def save_memory(self, memory_text):
        return self.long_term.add_important_memory(memory_text)

    def forget_memory(self, query):
        matches = self.long_term.archive_matching(query, "user_requested_forget")
        return bool(matches)

    def forget_all_memory(self):
        return self.long_term.archive_all("user_requested_forget_all")

    def search(self, query, limit=8, include_archived=False):
        return self.long_term.search(query, limit=limit, include_archived=include_archived)

    def get_archive(self):
        return self.long_term.get_archive()
