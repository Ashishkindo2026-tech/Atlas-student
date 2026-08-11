import json
import os


class Notes:

    def __init__(self):

        self.file = "tools/notes.json"

        if not os.path.exists(self.file):

            with open(self.file, "w") as f:

                json.dump([], f)

    def save_note(self, note):

        with open(self.file, "r") as f:

            notes = json.load(f)

        notes.append(note)

        with open(self.file, "w") as f:

            json.dump(notes, f, indent=4)

    def get_notes(self):

        with open(self.file, "r") as f:

            return json.load(f)