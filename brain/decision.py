class DecisionEngine:

    def decide(self, user_input):

        text = user_input.lower().strip()

        operators = ["+", "-", "*", "/", "%"]

        if any(op in text for op in operators):

            return "tool"

        if text.startswith("calculate"):

            return "tool"

        if text.startswith("save note"):

            return "tool"

        if text == "show notes":

            return "tool"

        if text == "my notes":

            return "tool"

        if "what do you know about me" in text:

            return "profile"

        if "who am i" in text:

            return "profile"

        if "summarize me" in text:

            return "profile"

        return "reasoning"