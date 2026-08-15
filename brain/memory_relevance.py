from memory.memory_search import search_memory


class MemoryRelevance:
    """Ranks memories for the current request using the unified retrieval engine."""

    def __init__(self, minimum_score=0.18):
        self.minimum_score = minimum_score

    def find(self, user_input, limit=8, include_archived=False):
        memories = search_memory(user_input, limit=limit, include_archived=include_archived)
        return [memory for memory in memories if memory.get("score", 0.0) >= self.minimum_score]

    def best(self, user_input):
        memories = self.find(user_input, limit=1)
        return memories[0] if memories else None
