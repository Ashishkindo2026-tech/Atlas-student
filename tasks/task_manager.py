import json
import os


class TaskManager:

    def __init__(self):

        self.file = "tasks/tasks.json"

        if not os.path.exists("tasks"):

            os.makedirs("tasks")

        if not os.path.exists(self.file):

            with open(self.file, "w") as f:

                json.dump([], f)

    def get_tasks(self):

        with open(self.file, "r") as f:

            return json.load(f)

    def save_tasks(self, tasks):

        with open(self.file, "w") as f:

            json.dump(
                tasks,
                f,
                indent=4
            )

    def add_task(self, task):

        tasks = self.get_tasks()

        tasks.append(
            {
                "task": task,
                "completed": False
            }
        )

        self.save_tasks(tasks)

    def complete_task(self, number):

        tasks = self.get_tasks()

        if (
            number < 1
            or
            number > len(tasks)
        ):

            return False

        tasks[number - 1][
            "completed"
        ] = True

        self.save_tasks(tasks)

        return True