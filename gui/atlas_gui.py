import customtkinter as ctk
import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from llm.ollama_client import Ollama_Client
from memory.history import add_message, get_recent_messages

ctk.set_appearance_mode("dark")

llm = Ollama_Client()

app = ctk.CTk()
app.title("Atlas AI")
app.geometry("1000x700")

title = ctk.CTkLabel(
    app,
    text="🧠 Atlas",
    font=("Arial", 30, "bold")
)
title.pack(pady=10)

chat_box = ctk.CTkTextbox(
    app,
    width=900,
    height=500
)
chat_box.pack(pady=10)

input_frame = ctk.CTkFrame(app)
input_frame.pack(fill="x", padx=20, pady=10)

user_input = ctk.CTkEntry(
    input_frame,
    width=700
)
user_input.pack(side="left", padx=10)


def send_message():

    user = user_input.get().strip()

    if not user:
        return

    chat_box.insert("end", f"\nYou: {user}\n")

    add_message("User", user)

    history = get_recent_messages(20)

    history_text = ""

    for msg in history:
        history_text += (
            f"{msg['role']}: "
            f"{msg['message']}\n"
        )

    prompt = f"""
You are Atlas.

Creator: Ashish

Rules:
- You are Atlas.
- Never say you are Qwen.
- Never mention Alibaba Cloud.
- You were created by Ashish.

Conversation History:
{history_text}

User:
{user}

Atlas:
"""

    response = llm.ask(prompt)

    response = response.replace(
        "Qwen",
        "Atlas"
    )

    add_message("Atlas", response)

    chat_box.insert(
        "end",
        f"Atlas: {response}\n"
    )

    user_input.delete(0, "end")


send_btn = ctk.CTkButton(
    input_frame,
    text="Send",
    command=send_message
)

send_btn.pack(side="left", padx=10)

app.mainloop()