class ProfileBuilder:

    def build(self, memory, goal_manager):

        name = memory.recall("name") or "Unknown"

        color = (
            memory.recall("favorite_color")
            or "Unknown"
        )

        subject = (
            memory.recall("favorite_subject")
            or "Unknown"
        )

        goals = goal_manager.get_goals()

        memories = (
            memory.get_important_memories()
        )

        result = "\n=== USER KNOWLEDGE ===\n\n"

        result += f"Name: {name}\n"

        result += (
            f"Favorite Color: {color}\n"
        )

        result += (
            f"Favorite Subject: {subject}\n\n"
        )

        result += "Goals:\n"

        if goals:

            for i, goal in enumerate(
                goals,
                1
            ):

                result += (
                    f"{i}. {goal}\n"
                )

        else:

            result += (
                "No goals stored.\n"
            )

        result += (
            "\nImportant Memories:\n"
        )

        if memories:

            for i, item in enumerate(
                memories,
                1
            ):

                result += (
                    f"{i}. {item}\n"
                )

        else:

            result += (
                "No important memories.\n"
            )

        return result