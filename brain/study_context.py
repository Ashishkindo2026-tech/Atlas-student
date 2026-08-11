from study.book_search import search_books
from study.notes_manager import search_notes


def build_study_context(user_input):
    """
    Searches study material only.

    Personal memory is NOT used here.
    """

    results = []

    # ==========================================
    # SEARCH BOOKS
    # ==========================================

    try:
        book_results = search_books(user_input)

        if book_results:
            for item in book_results:
                results.append({
                    "type": "book",
                    "content": item
                })

    except Exception as e:
        print(f"[DEBUG] Book search unavailable: {e}")

    # ==========================================
    # SEARCH NOTES
    # ==========================================

    try:
        note_results = search_notes(user_input)

        if note_results:
            for item in note_results:
                results.append({
                    "type": "note",
                    "content": item
                })

    except Exception as e:
        print(f"[DEBUG] Notes search unavailable: {e}")

    return results