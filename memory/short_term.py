class ShortTermMemory:

    def __init__(self):
        self.data = {}

    def remember(self, key, value):
        self.data[key] = value

    def recall(self, key):
        return self.data.get(key)