from tools.calculator import Calculator
from tools.notes import Notes
from tools.task_tool import TaskTool
from tools.project_tool import ProjectTool


class ToolManager:

    def __init__(self):

        self.calculator = Calculator()

        self.notes = Notes()

        self.tasks = TaskTool()

        self.projects = ProjectTool()

    def handle(self, user_input):

        text = user_input.lower().strip()

        # PROJECTS

        project_result = self.projects.handle(
            user_input
        )

        if project_result:

            return project_result

        # TASKS

        task_result = self.tasks.handle(
            user_input
        )

        if task_result:

            return task_result

        # CALCULATOR

        if text.startswith("calculate"):

            expression = (
                user_input[9:].strip()
            )

            return (
                self.calculator.calculate(
                    expression
                )
            )

        operators = [
            "+",
            "-",
            "*",
            "/",
            "%"
        ]

        if any(
            op in text
            for op in operators
        ):

            return (
                self.calculator.calculate(
                    text
                )
            )

        # NOTES

        if text.startswith(
            "save note"
        ):

            note = (
                user_input[9:].strip()
            )

            self.notes.save_note(
                note
            )

            return (
                f"Note saved: {note}"
            )

        elif (
            text == "show notes"
            or
            text == "my notes"
        ):

            notes = (
                self.notes.get_notes()
            )

            if not notes:

                return (
                    "No notes saved."
                )

            result = (
                "\n=== NOTES ===\n\n"
            )

            for i, note in enumerate(
                notes,
                1
            ):

                result += (
                    f"{i}. {note}\n"
                )

            return result

        return None