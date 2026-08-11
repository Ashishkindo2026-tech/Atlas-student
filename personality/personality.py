import json

class Personality:

    def __init__(self):

        with open(
            "personality/personality.json",
            "r",
            encoding="utf-8"
        ) as f:

            self.data = json.load(f)

    def get(self):

        return self.data