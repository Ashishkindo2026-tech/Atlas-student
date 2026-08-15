from memory.memory_manager import MemoryManager


def search_memory(query, limit=10, include_archived=False):
    """Hybrid lexical/metadata retrieval from the unified memory store."""
    return MemoryManager().search(query, limit=limit, include_archived=include_archived)
