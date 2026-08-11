import json
import os

MEMORY_FILE = "memory/data.json"


def load_memory():

    print("[DEBUG] Loading memory...")

    if not os.path.exists(MEMORY_FILE):
        print("[DEBUG] Memory file not found.")
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("[DEBUG] Memory loaded successfully.")
        print("[DEBUG] Data:", data)

        return data

    except Exception as e:
        print("[ERROR] Failed to load memory.")
        print("[ERROR]", e)
        return {}


def save_memory(data):

    print("[DEBUG] Saving memory...")

    try:
        os.makedirs("memory", exist_ok=True)

        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print("[DEBUG] Memory saved successfully.")

    except Exception as e:
        print("[ERROR] Failed to save memory.")
        print("[ERROR]", e)


def remember(key, value):

    print(f"[DEBUG] Remembering: {key} = {value}")

    data = load_memory()

    data[key] = value

    save_memory(data)


def recall(key):

    print(f"[DEBUG] Recalling: {key}")

    data = load_memory()

    value = data.get(key)

    print(f"[DEBUG] Found: {value}")

    return value


def clear_memory():

    print("[DEBUG] Clearing memory...")

    save_memory({})

    print("[DEBUG] Memory cleared.")