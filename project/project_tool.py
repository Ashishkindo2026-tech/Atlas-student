from project.project_manager import ProjectManager


class ProjectTool:
    def __init__(self):
        self.projects = ProjectManager()

    def handle(self, user_input: str):

        if not user_input:
            return "❌ Empty command"

        text = user_input.lower().strip()

        # Create project
        if text.startswith("create project"):
            name = user_input[len("create project"):].strip()

            if not name:
                return "❌ Project name missing!"

            return self.projects.create_project(name)

        # List projects
        elif text == "list projects":
            return self.projects.list_projects()

        # Open project
        elif text.startswith("open project"):
            name = user_input[len("open project"):].strip()

            if not name:
                return "❌ Project name missing!"

            return self.projects.open_project(name)

        return "❌ Command not recognized"