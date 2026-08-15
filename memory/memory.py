from memory.memory_manager import MemoryManager


_manager = MemoryManager()


def load_memory():
    """Return the legacy fact mapping, backed by the unified memory store."""
    return _manager.get_facts()


def save_memory(data):
    """Replace legacy facts while keeping all records in unified storage."""
    if not isinstance(data, dict):
        raise TypeError("Memory data must be a dictionary")
    current = _manager.get_facts()
    for key in list(current):
        if key not in data:
            _manager.delete_fact(key)
    for key, value in data.items():
        _manager.remember(key, value, source="legacy_api")


def remember(key, value):
    return _manager.remember(key, value)


def recall(key):
    return _manager.recall(key)


def clear_memory():
    _manager.delete_all_memory()
