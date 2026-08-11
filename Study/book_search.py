import os
import re


BOOKS_FOLDER = "study/books"


def _keywords(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    stop_words = {
        "what", "is", "the", "a", "an",
        "of", "to", "and", "in", "on",
        "for", "me", "tell", "about",
        "my", "please", "explain"
    }

    return [
        word
        for word in words
        if word not in stop_words
        and len(word) > 2
    ]


def search_books(query):

    if not os.path.exists(BOOKS_FOLDER):
        return []

    query_words = _keywords(query)

    results = []

    for filename in os.listdir(BOOKS_FOLDER):

        path = os.path.join(
            BOOKS_FOLDER,
            filename
        )

        if not os.path.isfile(path):
            continue

        if not filename.lower().endswith(".txt"):
            continue

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                text = file.read()

        except Exception:
            continue

        searchable = text.lower()

        score = 0

        for word in query_words:

            if word in searchable:
                score += 1

        if score > 0:

            results.append({
                "type": "book",
                "book": filename,
                "text": text,
                "score": score
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results