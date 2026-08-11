from brain.agent import process
from voice.voice_mode import run_voice_mode
from tools.system_tools import *
from voice.voice_engine import speak, listen
from llm.ollama_client import Ollama_Client
from education.library_watcher import scan_and_ingest

from memory.memory import remember, recall
from memory.history import (
    add_message,
    get_recent_messages
)

from project.project_manager import (
    create_project,
    add_task,
    list_projects,
    delete_project
)

# --------------------------------
# Startup
# --------------------------------

print("[DEBUG] Atlas starting...")

try:
    name = recall("name")
    if name:
        print(f"Welcome back, {name}!")
    else:
        print("Welcome to Atlas.")
except Exception as e:
    print("[STARTUP ERROR]", e)

# --------------------------------
# Automatic education library import
# --------------------------------

try:
    imported = scan_and_ingest()
    successful = [item for item in imported if "error" not in item]
    failed = [item for item in imported if "error" in item]
    if successful:
        print(f"[EDUCATION] Indexed {len(successful)} book(s) from the local Class 9-12 library.")
    if failed:
        for item in failed:
            print(f"[EDUCATION ERROR] {item.get('path', 'unknown')}: {item['error']}")
except Exception as e:
    print("[EDUCATION STARTUP ERROR]", type(e).__name__, e)

# --------------------------------
# Load LLM
# --------------------------------

print("[DEBUG] Loading LLM...")

try:
    llm = Ollama_Client()
    print("[DEBUG] LLM loaded.")
except Exception as e:
    print("[LLM ERROR]", e)
    exit()

print("🧠 Atlas v5 Online")

# --------------------------------
# Main Loop
# --------------------------------
while True:
    try:
        user = input("You: ").strip()

        if not user:
            continue

        # --------------------------
        # Exit
        # --------------------------
        if user.lower() in ["exit", "quit"]:
            print("Atlas: Goodbye 👋")
            break

        # --------------------------
        # Identity
        # --------------------------
        if user.lower() == "who are you":
            print("Atlas: I am Atlas.")
            continue
        if user.lower() == "what is your name":
            print("Atlas: My name is Atlas.")
            continue
        if user.lower() == "who created you":
            print("Atlas: I was created by Ashish.")
            continue

        # --------------------------
        # Name Memory
        # --------------------------
        if user.lower().startswith("my name is "):
            name = user[11:].strip()
            remember("name", name)
            print(f"Atlas: Nice to meet you, {name}. I'll remember that.")
            continue

        if user.lower() == "what is my name":
            name = recall("name")
            print(f"Atlas: Your name is {name}." if name else "Atlas: I don't know your name yet.")
            continue

        # --------------------------
        # Project System
        # --------------------------
        if user.lower().startswith("create project "):
            project_name = user[15:].strip()
            print(f"Atlas: Project '{project_name}' created." if create_project(project_name) else "Atlas: Project already exists.")
            continue

        if user.lower().startswith("delete project "):
            project_name = user[15:].strip()
            print("Atlas: Project deleted." if delete_project(project_name) else "Atlas: Project not found.")
            continue

        if user.lower() == "list projects":
            projects = list_projects()
            if not projects:
                print("Atlas: No projects found.")
            else:
                print("\nProjects:\n")
                for name, data in projects.items():
                    print(name)
                    for task in data["tasks"]:
                        print(f"  - {task}")
                    print()
            continue

        if user.lower().startswith("add task "):
            try:
                parts = user[9:].split(" to ")
                task = parts[0].strip()
                project = parts[1].strip()
                print("Atlas: Task added." if add_task(project, task) else "Atlas: Project not found.")
            except Exception:
                print("Atlas: Use -> add task <task> to <project>")
            continue

        # --------------------------
        # System Tools
        # --------------------------
        if user.lower() == "open notepad":
            open_notepad()
            print("Atlas: Opening Notepad.")
            continue
        if user.lower() == "open calculator":
            open_calculator()
            print("Atlas: Opening Calculator.")
            continue
        if user.lower() == "open paint":
            open_paint()
            print("Atlas: Opening Paint.")
            continue
        if user.lower() == "open cmd":
            open_cmd()
            print("Atlas: Opening Command Prompt.")
            continue
        if user.lower() == "open youtube":
            open_youtube()
            print("Atlas: Opening YouTube.")
            continue
        if user.lower() == "open google":
            open_google()
            print("Atlas: Opening Google.")
            continue
        if user.lower() == "what time is it":
            print("Atlas:", get_time())
            continue
        if user.lower() == "voice mode":
            run_voice_mode(llm)
            continue
        if user.lower() == "what is today's date":
            print("Atlas:", get_date())
            continue

        # --------------------------
        # Conversation History
        # --------------------------
        history = get_recent_messages(50)
        history_text = ""
        for msg in history:
            history_text += f"{msg['role']}: {msg['message']}\n"

        prompt = f"""
You are Atlas.

Creator: Ashish

Rules:
- You are Atlas.
- Never say you are Qwen.
- Never say you are developed by Alibaba Cloud.
- Never mention Alibaba Cloud.
- Always identify yourself as Atlas.
- You were created by Ashish.
- Be intelligent and helpful.

Conversation History:
{history_text}

User:
{user}

Atlas:
"""

        add_message("User", user)

        # Ask Agent First
        agent_response = process(user)
        response = agent_response if agent_response else llm.ask(prompt)

        # Identity Protection
        response = response.replace("Qwen", "Atlas")
        response = response.replace("qwen", "Atlas")
        response = response.replace("Alibaba Cloud", "Ashish")
        response = response.replace("developed by Alibaba Cloud", "created by Ashish")
        response = response.replace("created by Alibaba Cloud", "created by Ashish")

        add_message("Atlas", response)
        print("Atlas:", response)

    except Exception as e:
        print("\n[RUNTIME ERROR]")
        print(type(e).__name__)
        print(e)
