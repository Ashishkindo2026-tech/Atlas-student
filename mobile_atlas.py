"""Atlas Student local-LAN mobile/browser interface sharing the desktop brain."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from brain.agent import AtlasAgent
from atlas_core.config import CONFIG


app = FastAPI(title="Atlas Student Mobile", version="1.1")
agent = AtlasAgent()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    html_path = Path(__file__).with_name("mobile_atlas.html")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/status")
def status():
    return {
        "online": True,
        "model": CONFIG.ollama_model,
        "name": "Atlas Student",
        "transport": "local-LAN",
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        return {"response": str(agent.process(message))}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Atlas brain unavailable: {exc}") from exc


@app.get("/api/learning")
def learning_status():
    try:
        return agent.student.dashboard()
    except AttributeError:
        # Keep compatibility with older AtlasAgent builds while the shared
        # brain still remains the single chat path.
        from student.atlas_student import AtlasStudentSystem
        return AtlasStudentSystem().dashboard()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Learning state unavailable: {exc}") from exc


if __name__ == "__main__":
    # 0.0.0.0 is required for same-Wi-Fi/LAN device access.
    # Keep this LAN-only unless authentication and HTTPS are deliberately added.
    uvicorn.run("mobile_atlas:app", host="0.0.0.0", port=8000, reload=False)
