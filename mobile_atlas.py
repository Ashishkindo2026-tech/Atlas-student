from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from llm.ollama_client import Ollama_Client
from memory.history import add_message, get_recent_messages


app = FastAPI(title="Atlas Student Mobile", version="1.0")
llm = Ollama_Client()


class ChatRequest(BaseModel):
    message: str


SYSTEM_PROMPT = """
You are Atlas Student, a personal AI assistant created by Ashish.

Rules:
- Always identify yourself as Atlas Student when identity is relevant.
- Never claim to be Qwen.
- Never mention Alibaba Cloud.
- Be helpful, clear, friendly, and student-focused.
- Use the conversation history when it is relevant.
""".strip()


def build_prompt(user_message: str) -> str:
    history = get_recent_messages(50)
    history_text = "\n".join(
        f"{item.get('role', 'User')}: {item.get('message', '')}"
        for item in history
    )
    return f"""{SYSTEM_PROMPT}

Conversation history:
{history_text}

User:
{user_message}

Atlas Student:
"""


@app.get("/", response_class=HTMLResponse)
def home():
    html_path = Path(__file__).with_name("mobile_atlas.html")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/status")
def status():
    return {"online": True, "model": llm.model, "name": "Atlas Student"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    add_message("User", message)
    response = llm.ask(build_prompt(message))

    # Keep Atlas identity consistent with the existing Atlas code.
    response = response.replace("Qwen", "Atlas Student")
    response = response.replace("qwen", "Atlas Student")
    response = response.replace("Alibaba Cloud", "Ashish")

    add_message("Atlas", response)
    return {"response": response}


if __name__ == "__main__":
    # 0.0.0.0 makes Atlas reachable by another device on the same Wi-Fi/LAN.
    # Keep this LAN-only unless you deliberately add authentication and HTTPS.
    uvicorn.run("mobile_atlas:app", host="0.0.0.0", port=8000, reload=False)
