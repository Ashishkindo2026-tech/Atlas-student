from tasks.task_manager import TaskManager


class TaskTool:

    def __init__(self):

        self.tasks = TaskManager()

    def handle(self, user_input):

        text = user_input.lower()

        if text.startswith("save task"):

            task = user_input[9:].strip()

            self.tasks.add_task(task)

            return (
                f"Task saved: {task}"
            )

        elif text == "show tasks":

            tasks = (
                self.tasks.get_tasks()
            )

            if not tasks:

                return (
                    "No tasks saved."
                )

            result = (
                "\n=== TASKS ===\n\n"
            )

            for i, task in enumerate(
                tasks,
                1
            ):

                status = "✅"

                if not task[
                    "completed"
                ]:

                    status = "⏳"

                result += (
                    f"{i}. {status} "
                    f"{task['task']}\n"
                )

            return result

        elif text.startswith(
            "complete task"
        ):

            try:

                number = int(
                    text.split()[-1]
                )

            except:

                return (
                    "Invalid task number."
                )

            success = (
                self.tasks.complete_task(
                    number
                )
            )

            if success:

                return (
                    f"Task {number} completed."
                )

            return (
                "Task not found."
            )

        return None