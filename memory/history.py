import json
import os

HISTORY_FILE = "memory/chat_history.json"


def initialize_history():

    os.makedirs("memory", exist_ok=True)

    if not os.path.exists(HISTORY_FILE):

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_history():

    initialize_history()

    try:

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

            return []

    except Exception as e:

        print("[HISTORY ERROR]", e)

        return []


def save_history(history):

    initialize_history()

    try:

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:

            json.dump(
                history,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        print("[HISTORY SAVE ERROR]", e)


def add_message(role, message):

    history = load_history()

    history.append({
        "role": role,
        "message": str(message)
    })

    save_history(history)


def get_recent_messages(limit=20):

    history = load_history()

    return history[-limit:]


def get_all_messages():

    return load_history()


def search_history(keyword):

    keyword = keyword.lower()

    results = []

    for msg in load_history():

        if keyword in msg["message"].lower():

            results.append(msg)

    return results


def clear_history():

    save_history([])

    print("[DEBUG] History cleared.")