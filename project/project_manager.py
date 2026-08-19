import json
import os

PROJECT_FILE = "projects/projects.json"


def load_projects():
    os.makedirs("projects", exist_ok=True)

    if not os.path.exists(PROJECT_FILE):
        save_projects({})

    try:
        with open(PROJECT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError, TypeError):
        # Preserve the broken file for diagnosis instead of silently destroying it.
        backup = PROJECT_FILE + ".corrupt"
        try:
            os.replace(PROJECT_FILE, backup)
        except OSError:
            pass
        data = {}
        save_projects(data)

    return data if isinstance(data, dict) else {}


def save_projects(data):
    if not isinstance(data, dict):
        raise TypeError("Project store must be a dictionary")

    os.makedirs(os.path.dirname(PROJECT_FILE) or ".", exist_ok=True)
    temp = PROJECT_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(temp, PROJECT_FILE)


def create_project(name):
    projects = load_projects()
    name = str(name).strip()
    if not name or name in projects:
        return False

    projects[name] = {"tasks": [], "notes": []}
    save_projects(projects)
    return True


def add_task(project, task):
    projects = load_projects()
    if project not in projects:
        return False

    projects[project].setdefault("tasks", []).append(task)
    save_projects(projects)
    return True


def list_projects():
    return load_projects()


def delete_project(name):
    projects = load_projects()
    if name in projects:
        del projects[name]
        save_projects(projects)
        return True
    return False
