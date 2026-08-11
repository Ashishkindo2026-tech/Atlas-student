class SelfReflection:

    def should_remember(self, text):

        text = text.lower()

        ignore = [

            "show profile",
            "show memories",
            "show important memories",
            "what are my goals",
            "what is my name",
            "show notes",
            "my notes",
            "calculate"
        ]

        for item in ignore:

            if item in text:

                return False

        important = [

            "my goal is",
            "my favorite",
            "remember",
            "project",
            "exam",
            "nda",
            "atlas"
        ]

        for item in important:

            if item in text:

                return True

        return False