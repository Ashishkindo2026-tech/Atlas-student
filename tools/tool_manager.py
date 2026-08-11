from tools.system_tools import get_time, get_date
from project.project_manager import list_projects

class ToolManager:
    """Small registry for deterministic local tools. The LLM does not execute tools directly."""
    def __init__(self):
        self.tools = {
            "time": get_time,
            "date": get_date,
            "projects": list_projects,
        }

    def available(self):
        return sorted(self.tools.keys())

    def run(self, name):
        if name not in self.tools:
            return None
        return self.tools[name]()

    def describe(self):
        return ", ".join(self.available())
