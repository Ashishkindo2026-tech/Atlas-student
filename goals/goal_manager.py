import json
import os


class GoalManager:

    def __init__(self):

        self.file = "goals/goals.json"

        if not os.path.exists(self.file):

            with open(self.file, "w") as f:

                json.dump(
                    {
                        "active_goals": [],
                        "completed_goals": []
                    },
                    f,
                    indent=4
                )

    def load(self):

        with open(self.file, "r") as f:

            return json.load(f)

    def save(self, data):

        with open(self.file, "w") as f:

            json.dump(data, f, indent=4)

    def add_goal(self, goal):

        data = self.load()

        if goal not in data["active_goals"]:

            data["active_goals"].append(goal)

            self.save(data)

    def get_goals(self):

        data = self.load()

        return data["active_goals"]

    def complete_goal(self, goal):

        data = self.load()

        if goal in data["active_goals"]:

            data["active_goals"].remove(goal)

            data["completed_goals"].append(goal)

            self.save(data)

    def get_completed_goals(self):

        data = self.load()

        return data["completed_goals"]