from project.project_manager import ProjectManager

class ProjectTool:
    def __init__(self):
        self.pm = ProjectManager()

    def handle(self, user_input):
        text = user_input.lower().strip()

        if text.startswith("create project"):
            name = user_input[len("create project"):].strip()
            if not name:
                return "❌ Project name missing!"
            return self.pm.create_project(name)

        elif text.startswith("list projects"):
            return self.pm.list_projects()

        return "❌ Unknown project command"
    