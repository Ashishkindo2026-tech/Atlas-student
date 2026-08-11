from memory.memory import load_memory
from memory.memory_manager import MemoryManager


STOP_WORDS = {
    "tell",
    "me",
    "about",
    "what",
    "is",
    "my",
    "the",
    "a",
    "an",
    "do",
    "you",
    "know",
    "remember",
    "please",
    "can",
    "could",
    "would",
    "and",
    "or",
    "of",
    "to",
    "for",
    "this",
    "that",
    "there",
    "your",
    "mine"
}


def _keywords(text):

    words = (
        text.lower()
        .replace("?", "")
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("'", "")
        .split()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    ]


def _calculate_score(query_words, text):

    words = set(
        text.lower()
        .replace("?", "")
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .split()
    )

    score = 0

    for word in query_words:

        if word in words:
            score += 1

    return score


def search_memory(query):

    query_words = _keywords(query)

    results = []

    # ==================================================
    # FACT MEMORY
    # ==================================================

    data = load_memory()

    for key, value in data.items():

        # Convert keys like:
        # favorite_subject
        # into:
        # favorite subject

        searchable = f"{key.replace('_', ' ')} {value}"

        score = _calculate_score(
            query_words,
            searchable
        )

        if score > 0:

            results.append({
                "type": "fact",
                "key": key,
                "value": value,
                "score": score
            })

    # ==================================================
    # IMPORTANT MEMORY
    # ==================================================

    manager = MemoryManager()

    important = manager.get_important_memories()

    for memory in important:

        score = _calculate_score(
            query_words,
            memory
        )

        if score > 0:

            results.append({
                "type": "important",
                "value": memory,
                "score": score
            })

    # ==================================================
    # SORT BY RELEVANCE
    # ==================================================

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results