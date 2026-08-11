import json
import os


class MemoryManager:

    def __init__(self):

        self.file = "memory/memory.json"

        self._initialize()

    # ==========================================
    # INITIALIZE
    # ==========================================

    def _initialize(self):

        os.makedirs("memory", exist_ok=True)

        default_data = {
            "facts": {},
            "important_memories": []
        }

        if not os.path.exists(self.file):

            self.save(default_data)

            return

        try:

            data = self.load()

            changed = False

            if not isinstance(data, dict):

                data = default_data

                changed = True

            if "facts" not in data:

                data["facts"] = {}

                changed = True

            if "important_memories" not in data:

                data["important_memories"] = []

                changed = True

            if changed:

                self.save(data)

        except Exception:

            self.save(default_data)

    # ==========================================
    # FILE
    # ==========================================

    def load(self):

        with open(
            self.file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def save(self, data):

        with open(
            self.file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

    # ==========================================
    # FACT MEMORY
    # ==========================================

    def remember(self, key, value):

        data = self.load()

        data["facts"][key] = value

        self.save(data)

    def recall(self, key):

        data = self.load()

        return data["facts"].get(key)

    def get_facts(self):

        data = self.load()

        return data["facts"]

    # ==========================================
    # IMPORTANT MEMORY
    # ==========================================

    def add_important_memory(self, text):

        data = self.load()

        if text not in data["important_memories"]:

            data["important_memories"].append(text)

            self.save(data)

    def get_important_memories(self):

        data = self.load()

        return data["important_memories"]

    # ==========================================
    # DELETE IMPORTANT MEMORY
    # ==========================================

    def delete_important_memory(self, text):

        data = self.load()

        if text in data["important_memories"]:

            data["important_memories"].remove(text)

            self.save(data)

            return True

        return False

    # ==========================================
    # DELETE FACT
    # ==========================================

    def delete_fact(self, key):

        data = self.load()

        if key in data["facts"]:

            del data["facts"][key]

            self.save(data)

            return True

        return False

    # ==========================================
    # DELETE ALL MEMORY
    # ==========================================

    def delete_all_memory(self):

        data = {
            "facts": {},
            "important_memories": []
        }

        self.save(data)

        return True