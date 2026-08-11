class ConversationLogger:

    def __init__(self):

        self.history = []

    def log(self, speaker, text):

        self.history.append(
            f"{speaker}: {text}"
        )

    def get_recent(self, limit=20):

        return "\n".join(
            self.history[-limit:]
        )