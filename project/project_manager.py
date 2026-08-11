import json
import os

PROJECT_FILE = "projects/projects.json"


def load_projects():

    os.makedirs("projects", exist_ok=True)

    if not os.path.exists(PROJECT_FILE):
        with open(PROJECT_FILE, "w") as f:
            json.dump({}, f)

    with open(PROJECT_FILE, "r") as f:
        return json.load(f)


def save_projects(data):

    with open(PROJECT_FILE, "w") as f:
        json.dump(data, f, indent=4)


def create_project(name):

    projects = load_projects()

    if name in projects:
        return False

    projects[name] = {
        "tasks": [],
        "notes": []
    }

    save_projects(projects)

    return True


def add_task(project, task):

    projects = load_projects()

    if project not in projects:
        return False

    projects[project]["tasks"].append(task)

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