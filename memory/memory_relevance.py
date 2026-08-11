from memory.memory_search import search_memory


class MemoryRelevance:

    def __init__(self, minimum_score=1):

        self.minimum_score = minimum_score

    def find(self, user_input):

        memories = search_memory(user_input)

        relevant = []

        for memory in memories:

            score = memory.get("score", 0)

            if score >= self.minimum_score:

                relevant.append(memory)

        return relevant

    def best(self, user_input):

        memories = self.find(user_input)

        if not memories:
            return None

        return memories[0]