"""ATLAS — Personal AI Learning System desktop interface.

Learning is the center of Atlas; chat and voice are capabilities inside the
system rather than the whole identity. Optional microphone/speech packages
are used when available and the UI remains usable in text-only mode.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import tkinter as tk
from datetime import datetime

from brain.agent import process
from student.atlas_student import system

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover
    sr = None

try:
    import edge_tts
    import pygame
except ImportError:  # pragma: no cover
    edge_tts = None
    pygame = None

BG = "#0b0f14"
PANEL = "#111720"
PANEL_2 = "#151d27"
BORDER = "#26313d"
TEXT = "#eef3f8"
MUTED = "#8e9aa8"
ACCENT = "#79d8c5"
DANGER = "#e47d7d"


class AtlasDashboard(tk.Tk):
    """Premium desktop dashboard with integrated text chat and voice."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ATLAS — Your learning system")
        self.geometry("1200x760")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.option_add("*Font", ("Segoe UI", 10))
        self.chat_messages: list[tuple[str, str]] = []
        self._voice_busy = False
        self._build()

    def _label(self, parent, text, size=10, weight="normal", color=TEXT, **kwargs):
        return tk.Label(parent, text=text, font=("Segoe UI", size, weight),
                        fg=color, bg=parent.cget("bg"), **kwargs)

    def _build(self) -> None:
        header = tk.Frame(self, bg=BG, height=72)
        header.pack(fill="x", padx=26, pady=(18, 0))
        header.pack_propagate(False)
        logo = tk.Canvas(header, width=34, height=34, bg=BG, highlightthickness=0)
        logo.pack(side="left", pady=10)
        logo.create_oval(5, 5, 29, 29, outline=ACCENT, width=2)
        logo.create_oval(13, 13, 21, 21, fill=ACCENT, outline="")
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left", padx=(10, 0))
        self._label(title_box, "ATLAS", 16, "bold").pack(anchor="w")
        self._label(title_box, "Your learning system", 9, color=MUTED).pack(anchor="w")
        status = tk.Frame(header, bg=BG)
        status.pack(side="right", pady=10)
        self._label(status, datetime.now().strftime("%a • %d %b %Y"), 9, color=MUTED).pack(side="left", padx=18)
        dot = tk.Canvas(status, width=10, height=10, bg=BG, highlightthickness=0)
        dot.pack(side="left")
        dot.create_oval(1, 1, 9, 9, fill=ACCENT, outline="")
        self._label(status, "ONLINE", 9, "bold", ACCENT).pack(side="left", padx=(6, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=26, pady=(0, 26))
        self.sidebar = tk.Frame(body, bg=PANEL, width=235, highlightbackground=BORDER, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True, padx=(22, 0))
        self._build_sidebar()
        self._show_dashboard()

    def _build_sidebar(self) -> None:
        self._label(self.sidebar, "TODAY", 9, "bold", MUTED).pack(anchor="w", padx=22, pady=(24, 12))
        for icon, name in (("◈", "Physics"), ("∑", "Maths"), ("◇", "Chemistry")):
            self._nav(icon, name, lambda n=name: self._show_subject(n))
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=18)
        self._nav("⌁", "Chat with Atlas", self._show_chat)
        self._nav("◉", "Voice with Atlas", self._show_voice)
        self._nav("⌘", "Memory", self._show_memory)
        self._nav("◒", "Progress", self._show_progress)
        self._nav("⚙", "Settings", self._show_settings)
        self._label(self.sidebar, "ATLAS CORE", 8, "bold", MUTED).pack(anchor="w", padx=22, pady=(28, 5))
        self._label(self.sidebar, "LOCAL • PRIVATE • READY", 8, color=ACCENT).pack(anchor="w", padx=22)

    def _nav(self, icon: str, text: str, command) -> None:
        button = tk.Button(self.sidebar, text=f"  {icon}    {text}", command=command,
                           anchor="w", relief="flat", bd=0, bg=PANEL, fg=TEXT,
                           activebackground=PANEL_2, activeforeground=ACCENT,
                           font=("Segoe UI", 10), padx=12, pady=9, cursor="hand2")
        button.pack(fill="x", padx=10, pady=1)
        button.bind("<Enter>", lambda e: button.configure(bg=PANEL_2))
        button.bind("<Leave>", lambda e: button.configure(bg=PANEL))

    def _clear(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _show_dashboard(self) -> None:
        self._clear()
        self._label(self.content, "GOOD AFTERNOON, ASHISH", 23, "bold").pack(anchor="w", pady=(34, 2))
        self._label(self.content, "What are we working on?", 11, color=MUTED).pack(anchor="w")
        actions = tk.Frame(self.content, bg=BG)
        actions.pack(fill="x", pady=(28, 30))
        cards = [
            ("HOMEWORK", "Get help solving a question", "⌁", self._homework),
            ("REVISE", "Review concepts and formulas", "↻", self._revise),
            ("PRACTICE", "Test your understanding", "✓", self._practice),
            ("CHAT", "Talk to Atlas about anything", "◌", self._show_chat),
        ]
        for title, desc, icon, command in cards:
            self._card(actions, title, desc, icon, command)
        self._label(self.content, "TODAY'S PROGRESS", 9, "bold", MUTED).pack(anchor="w")
        progress = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        progress.pack(fill="x", pady=(10, 0))
        top = tk.Frame(progress, bg=PANEL)
        top.pack(fill="x", padx=20, pady=(18, 10))
        self._label(top, "Overall learning progress", 10, color=MUTED).pack(side="left")
        self._label(top, "78%", 18, "bold", ACCENT).pack(side="right")
        self._progress_row(progress, "Physics", 72)
        self._progress_row(progress, "Mathematics", 81)
        self._progress_row(progress, "Chemistry", 76)
        tk.Frame(progress, bg=PANEL, height=10).pack()

    def _card(self, parent, title, desc, icon, command) -> None:
        card = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1,
                        width=205, height=135, cursor="hand2")
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        card.pack_propagate(False)
        self._label(card, icon, 22, color=ACCENT).pack(anchor="w", padx=18, pady=(16, 4))
        self._label(card, title, 11, "bold").pack(anchor="w", padx=18)
        self._label(card, desc, 9, color=MUTED, wraplength=175, justify="left").pack(anchor="w", padx=18, pady=(5, 0))
        card.bind("<Button-1>", lambda e, fn=command: fn())
        card.bind("<Enter>", lambda e: card.configure(bg=PANEL_2))
        card.bind("<Leave>", lambda e: card.configure(bg=PANEL))

    def _progress_row(self, parent, subject: str, value: int) -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=20, pady=7)
        self._label(row, subject, 10).pack(side="left")
        self._label(row, f"{value}%", 9, "bold", MUTED).pack(side="right")
        bar = tk.Canvas(row, height=6, bg=PANEL, highlightthickness=0)
        bar.pack(side="right", fill="x", expand=True, padx=20)
        bar.update_idletasks()
        width = max(1, bar.winfo_width())
        bar.create_rectangle(0, 0, width, 6, fill=BORDER, outline="")
        bar.create_rectangle(0, 0, width * value / 100, 6, fill=ACCENT, outline="")

    def _workspace(self, title: str, subtitle: str) -> None:
        self._clear()
        self._label(self.content, title, 22, "bold").pack(anchor="w", pady=(34, 2))
        self._label(self.content, subtitle, 10, color=MUTED).pack(anchor="w")
        panel = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True, pady=(24, 0))
        self._label(panel, "Atlas Core", 10, "bold", ACCENT).pack(anchor="w", padx=24, pady=(24, 4))
        self._label(panel, "This workspace is connected to your learning system.", 12).pack(anchor="w", padx=24)

    def _show_subject(self, subject: str) -> None:
        self._workspace(subject, f"Focused {subject} workspace")
    def _show_memory(self) -> None:
        self._workspace("Memory", "What Atlas knows about your learning journey")
    def _show_progress(self) -> None:
        self._workspace("Progress", "Learning analytics and weak-topic signals")
    def _show_settings(self) -> None:
        self._workspace("Settings", "Atlas Core, privacy, model and interface controls")
    def _mode(self, name: str) -> None:
        self._workspace(name, "Atlas is ready. Your learning stays at the center.")
    def _homework(self) -> None:
        self._mode("Homework Mode")
    def _revise(self) -> None:
        self._mode("Revision Mode")
    def _practice(self) -> None:
        self._mode("Practice Mode")

    def _show_chat(self) -> None:
        self._clear()
        self._label(self.content, "CHAT WITH ATLAS", 22, "bold").pack(anchor="w", pady=(30, 2))
        self._label(self.content, "Chat is a feature of Atlas. Learning stays at the center.", 10, color=MUTED).pack(anchor="w")
        frame = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, pady=(18, 0))
        self.chat_box = tk.Text(frame, bg=PANEL, fg=TEXT, insertbackground=ACCENT,
                                relief="flat", bd=0, wrap="word", font=("Segoe UI", 10), padx=22, pady=18)
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.tag_configure("user", foreground=ACCENT, font=("Segoe UI", 10, "bold"))
        self.chat_box.tag_configure("atlas", foreground=TEXT, font=("Segoe UI", 10))
        self.chat_box.configure(state="disabled")
        composer = tk.Frame(frame, bg=PANEL_2, height=58)
        composer.pack(fill="x", padx=12, pady=12)
        self.chat_entry = tk.Entry(composer, bg=PANEL_2, fg=TEXT, insertbackground=ACCENT,
                                   relief="flat", bd=0, font=("Segoe UI", 11))
        self.chat_entry.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        self.chat_entry.bind("<Return>", lambda e: self._send_chat())
        self._small_button(composer, "🎙", self._listen_once, "Voice input")
        self._small_button(composer, "SEND", self._send_chat, "Send message")
        self.chat_entry.focus_set()
        if not self.chat_messages:
            self._append_chat("Atlas", "I'm ready. Ask me a question, tell me what you're studying, or start a study session.")
        else:
            for speaker, text in self.chat_messages:
                self._append_chat(speaker, text, remember=False)

    def _small_button(self, parent, text, command, tooltip="") -> None:
        tk.Button(parent, text=text, command=command, bg=PANEL, fg=TEXT,
                  activebackground=ACCENT, activeforeground=BG, relief="flat", bd=0,
                  padx=14, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="right", padx=4)

    def _append_chat(self, speaker: str, text: str, remember: bool = True) -> None:
        if not hasattr(self, "chat_box"):
            return
        if remember:
            self.chat_messages.append((speaker, text))
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{speaker}\n", "user" if speaker == "You" else "atlas")
        self.chat_box.insert("end", f"{text}\n\n", "atlas")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _send_chat(self) -> None:
        text = self.chat_entry.get().strip()
        if not text:
            return
        self.chat_entry.delete(0, "end")
        self._append_chat("You", text)
        threading.Thread(target=self._answer_worker, args=(text,), daemon=True).start()

    def _answer_worker(self, text: str) -> None:
        try:
            answer = system.handle(text)
            if answer is None:
                answer = process(text)
            answer = str(answer)
        except Exception as exc:  # keep GUI alive if optional runtime services fail
            answer = f"Atlas Core could not complete that request: {exc}"
        self.after(0, lambda: self._append_chat("Atlas", answer))

    def _show_voice(self) -> None:
        self._clear()
        self._label(self.content, "VOICE WITH ATLAS", 22, "bold").pack(anchor="w", pady=(30, 2))
        self._label(self.content, "Speak naturally. Atlas can listen and answer aloud when voice support is installed.",
                    10, color=MUTED).pack(anchor="w")
        panel = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True, pady=(18, 0))
        orb = tk.Canvas(panel, width=180, height=180, bg=PANEL, highlightthickness=0)
        orb.pack(pady=(45, 15))
        orb.create_oval(20, 20, 160, 160, outline=ACCENT, width=2)
        orb.create_oval(65, 65, 115, 115, fill=ACCENT, outline="")
        self.voice_status = self._label(panel, "ATLAS CORE • READY", 11, "bold", ACCENT)
        self.voice_status.pack(pady=6)
        self._label(panel, "Press the microphone to speak. Your message will also appear in Chat.", 10, color=MUTED).pack(pady=4)
        tk.Button(panel, text="🎙  SPEAK TO ATLAS", command=self._listen_once,
                  bg=ACCENT, fg=BG, activebackground=TEXT, activeforeground=BG,
                  relief="flat", bd=0, padx=24, pady=12, cursor="hand2",
                  font=("Segoe UI", 10, "bold")).pack(pady=22)

    def _listen_once(self) -> None:
        if self._voice_busy:
            return
        if sr is None:
            self._set_voice_status("SpeechRecognition is not installed", DANGER)
            return
        self._voice_busy = True
        self._set_voice_status("LISTENING…", ACCENT)
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self) -> None:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=20)
            text = recognizer.recognize_google(audio)
            self.after(0, lambda: self._voice_received(text))
        except Exception as exc:
            self.after(0, lambda: self._set_voice_status(f"Voice input unavailable: {exc}", DANGER))
        finally:
            self._voice_busy = False

    def _voice_received(self, text: str) -> None:
        self._set_voice_status("THINKING…", ACCENT)
        self._append_voice_to_chat(text)
        threading.Thread(target=self._answer_voice_worker, args=(text,), daemon=True).start()

    def _append_voice_to_chat(self, text: str) -> None:
        self.chat_messages.append(("You", text))

    def _answer_voice_worker(self, text: str) -> None:
        try:
            answer = system.handle(text)
            if answer is None:
                answer = process(text)
            answer = str(answer)
            self.chat_messages.append(("Atlas", answer))
            self.after(0, lambda: self._set_voice_status("ATLAS CORE • READY", ACCENT))
            self._speak(answer)
        except Exception as exc:
            self.after(0, lambda: self._set_voice_status(f"Atlas error: {exc}", DANGER))

    def _speak(self, text: str) -> None:
        if edge_tts is None or pygame is None:
            return
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as handle:
                path = handle.name
            asyncio.run(edge_tts.Communicate(text, "en-IN-NeerjaNeural").save(path))
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            pygame.mixer.quit()
        except Exception:
            pass
        finally:
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _set_voice_status(self, text: str, color: str) -> None:
        if hasattr(self, "voice_status"):
            self.voice_status.configure(text=text, fg=color)


if __name__ == "__main__":
    AtlasDashboard().mainloop()
