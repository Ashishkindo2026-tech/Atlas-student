"""Atlas Student — Learning OS desktop interface.

The GUI keeps learning at the center: chat and voice are tools inside Atlas,
not the entire product. It is intentionally local-first and connects to the
existing Atlas brain, memory, progress and education modules.
"""
from __future__ import annotations

import os
import sys
import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from brain.agent import process

try:
    from voice_engine import listen, speak
    VOICE_AVAILABLE = True
except Exception:
    listen = speak = None
    VOICE_AVAILABLE = False

try:
    from memory.memory_manager import MemoryManager
except Exception:
    MemoryManager = None

try:
    from student.progress_manager import ProgressManager
except Exception:
    ProgressManager = None

try:
    from education.ingest import ingest_pdf
except Exception:
    ingest_pdf = None

# Atlas visual language: quiet, technical, premium.
BG = "#080A0F"
RAIL = "#06080C"
PANEL = "#10141B"
PANEL_2 = "#141923"
PANEL_3 = "#1A202C"
TEXT = "#F4F6FA"
MUTED = "#8993A5"
ACCENT = "#86A4FF"
ACCENT_2 = "#A8BAFF"
ACCENT_DARK = "#263554"
SUCCESS = "#70D2A5"
WARNING = "#E6B86A"
DANGER = "#E58D8D"
BORDER = "#252C39"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AtlasGUI(ctk.CTk):
    """Desktop Learning OS for Atlas Student."""

    def __init__(self):
        super().__init__()
        self.title("ATLAS — Personal AI Learning System")
        self.geometry("1440x900")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)
        self.current_page = "home"
        self.voice_busy = False
        self.chat_busy = False
        self.command_overlay = None
        self.chat_messages: list[tuple[str, str]] = []
        self.progress = ProgressManager() if ProgressManager else None
        self.memory = MemoryManager() if MemoryManager else None
        self._build_shell()
        self.bind("<Control-space>", lambda _e: self.toggle_command_center())
        self.bind("<Escape>", lambda _e: self.close_command_center())
        self.show_home()

    # ---------- shell ----------
    def _build_shell(self):
        self.rail = ctk.CTkFrame(self, width=230, fg_color=RAIL, corner_radius=0)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        brand = ctk.CTkFrame(self.rail, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(24, 28))
        ctk.CTkLabel(brand, text="◉", text_color=ACCENT, font=("Segoe UI Symbol", 25, "bold")).pack(side="left")
        labels = ctk.CTkFrame(brand, fg_color="transparent")
        labels.pack(side="left", padx=10)
        ctk.CTkLabel(labels, text="ATLAS", text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ctk.CTkLabel(labels, text="PERSONAL LEARNING OS", text_color=MUTED, font=("Segoe UI", 7, "bold")).pack(anchor="w")

        self.status = ctk.CTkFrame(self.rail, fg_color=PANEL, corner_radius=12)
        self.status.pack(fill="x", padx=16, pady=(0, 18))
        ctk.CTkLabel(self.status, text="●", text_color=SUCCESS, font=("Segoe UI", 10)).pack(side="left", padx=(12, 5), pady=9)
        ctk.CTkLabel(self.status, text="ATLAS CORE  •  ONLINE", text_color=MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")

        ctk.CTkLabel(self.rail, text="COMMAND CENTER", text_color="#626C7D", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(4, 8))
        self.nav_buttons = {}
        nav = [
            ("⌂", "Home", self.show_home),
            ("◈", "Chat", self.show_chat),
            ("◉", "Voice", self.show_voice),
        ]
        for icon, label, command in nav:
            self._nav_button(icon, label, command)

        ctk.CTkLabel(self.rail, text="LEARNING", text_color="#626C7D", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(18, 8))
        for icon, label, command in [
            ("Φ", "Physics", lambda: self.show_subject("Physics")),
            ("∑", "Maths", lambda: self.show_subject("Mathematics")),
            ("⚗", "Chemistry", lambda: self.show_subject("Chemistry")),
            ("▣", "Notes", self.show_notes),
            ("◇", "Practice", self.show_practice),
            ("◫", "Planner", self.show_planner),
        ]:
            self._nav_button(icon, label, command)

        ctk.CTkLabel(self.rail, text="INSIGHTS", text_color="#626C7D", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(18, 8))
        for icon, label, command in [
            ("◌", "Memory", self.show_memory),
            ("▥", "Progress", self.show_progress),
        ]:
            self._nav_button(icon, label, command)

        self._nav_button("⚙", "Settings", self.show_settings, bottom=True)

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def _nav_button(self, icon, label, command, bottom=False):
        b = ctk.CTkButton(
            self.rail, text=f"  {icon}    {label}", command=command,
            anchor="w", height=38, fg_color="transparent", hover_color=PANEL_2,
            text_color=MUTED, corner_radius=10, font=("Segoe UI", 10, "bold"),
        )
        b.pack(side="bottom" if bottom else "top", fill="x", padx=12, pady=2)
        self.nav_buttons[label] = b

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, eyebrow, title, subtitle=""):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=46, pady=(30, 20))
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text=eyebrow.upper(), text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=title, text_color=TEXT, font=("Segoe UI", 29, "bold")).pack(anchor="w", pady=(3, 0))
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(top, text=datetime.now().strftime("%a  •  %d %b %Y"), text_color=MUTED, font=("Segoe UI", 9, "bold")).pack(side="right", anchor="n")

    def card(self, parent, color=PANEL, radius=18):
        return ctk.CTkFrame(parent, fg_color=color, corner_radius=radius, border_width=1, border_color=BORDER)

    def button(self, parent, text, command, width=140, primary=False):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=40,
                             corner_radius=12, fg_color=ACCENT if primary else PANEL_3,
                             hover_color=ACCENT_2 if primary else "#232B3A",
                             text_color=BG if primary else TEXT, font=("Segoe UI", 10, "bold"))

    def set_active(self, label):
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=ACCENT_DARK if name == label else "transparent", text_color=TEXT if name == label else MUTED)

    # ---------- home ----------
    def show_home(self):
        self.current_page = "home"; self.set_active("Home"); self.clear()
        self.header("Atlas Core", "Good afternoon, Ashish.", "What are we working on?")
        body = ctk.CTkFrame(self.main, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=46, pady=(0, 36))
        body.grid_columnconfigure(0, weight=3); body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(1, weight=1)

        welcome = self.card(body, PANEL, 22); welcome.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(welcome, text="ATLAS CORE", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(welcome, text="Your learning system is ready.", text_color=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=24)
        ctk.CTkLabel(welcome, text="Chat is a feature of Atlas. Learning is the center of Atlas.", text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(3, 16))
        actions = ctk.CTkFrame(welcome, fg_color="transparent"); actions.pack(fill="x", padx=20, pady=(0, 18))
        for title, desc, cmd in [("💬  CHAT", "Ask Atlas", self.show_chat), ("◉  VOICE", "Talk naturally", self.show_voice), ("◇  PRACTICE", "Test yourself", self.show_practice), ("▣  NOTES", "Capture knowledge", self.show_notes)]:
            a = self.card(actions, PANEL_2, 14); a.pack(side="left", fill="x", expand=True, padx=4)
            self.button(a, title, cmd, width=120, primary=title.startswith("💬")).pack(pady=(12, 3))
            ctk.CTkLabel(a, text=desc, text_color=MUTED, font=("Segoe UI", 8)).pack(pady=(0, 12))

        left = self.card(body, PANEL, 20); left.grid(row=1, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(left, text="TODAY'S PROGRESS", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(22, 3))
        ctk.CTkLabel(left, text="78%", text_color=TEXT, font=("Segoe UI", 38, "bold")).pack(anchor="w", padx=22)
        bar = ctk.CTkProgressBar(left, height=8, progress_color=ACCENT, fg_color=BORDER); bar.pack(fill="x", padx=22, pady=(7, 20)); bar.set(.78)
        for subject, value in [("Physics", .72), ("Mathematics", .81), ("Chemistry", .76)]: self._progress_row(left, subject, value)

        right = self.card(body, PANEL, 20); right.grid(row=1, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(right, text="ATLAS INSIGHT", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(22, 8))
        ctk.CTkLabel(right, text="Your next best move", text_color=TEXT, font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=22)
        ctk.CTkLabel(right, text="Review a weak concept, then practice it. Atlas can adapt the next questions to your learning signals.", text_color=MUTED, wraplength=390, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=22, pady=(8, 20))
        self.button(right, "Open Practice Lab", self.show_practice, width=180, primary=True).pack(anchor="w", padx=22)

    def _progress_row(self, parent, subject, value):
        row = ctk.CTkFrame(parent, fg_color="transparent"); row.pack(fill="x", padx=22, pady=7)
        ctk.CTkLabel(row, text=subject, text_color=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left")
        ctk.CTkLabel(row, text=f"{int(value*100)}%", text_color=MUTED, font=("Segoe UI", 9)).pack(side="right")
        b = ctk.CTkProgressBar(parent, height=5, progress_color=ACCENT, fg_color=BORDER); b.pack(fill="x", padx=22); b.set(value)

    # ---------- chat ----------
    def show_chat(self):
        self.current_page = "chat"; self.set_active("Chat"); self.clear()
        self.header("Atlas Core", "Chat with Atlas", "Ask, learn, save, practice — all connected to the same learning system.")
        panel = self.card(self.main, PANEL, 20); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        self.chat_box = ctk.CTkTextbox(panel, fg_color="transparent", text_color=TEXT, font=("Segoe UI", 11), wrap="word")
        self.chat_box.pack(fill="both", expand=True, padx=20, pady=20); self.chat_box.configure(state="disabled")
        if not self.chat_messages: self._chat_add("ATLAS", "I'm ready. What are we learning?")
        else:
            for who, msg in self.chat_messages: self._chat_add(who, msg, store=False)
        bottom = ctk.CTkFrame(panel, fg_color=PANEL_2, corner_radius=14); bottom.pack(fill="x", padx=16, pady=(0, 16))
        self.chat_input = ctk.CTkEntry(bottom, placeholder_text="Ask Atlas anything...", height=44, fg_color="transparent", border_width=0, text_color=TEXT)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=12); self.chat_input.bind("<Return>", lambda _e: self.send_chat())
        self.button(bottom, "🎙", self.show_voice, width=48).pack(side="left", padx=4)
        self.button(bottom, "Send  ➜", self.send_chat, width=95, primary=True).pack(side="right", padx=6)

    def _chat_add(self, who, msg, store=True):
        if store: self.chat_messages.append((who, msg))
        if not hasattr(self, "chat_box"): return
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"\n{who}\n{msg}\n")
        self.chat_box.configure(state="disabled"); self.chat_box.see("end")

    def send_chat(self):
        if self.chat_busy or not hasattr(self, "chat_input"): return
        text = self.chat_input.get().strip()
        if not text: return
        self.chat_input.delete(0, "end"); self._chat_add("YOU", text)
        self.chat_busy = True
        self._chat_add("ATLAS", "Thinking…")
        threading.Thread(target=self._chat_worker, args=(text,), daemon=True).start()

    def _chat_worker(self, text):
        try: answer = process(text)
        except Exception as exc: answer = f"I hit an error while processing that: {exc}"
        self.after(0, lambda a=answer: self._finish_chat(a))

    def _finish_chat(self, answer):
        self.chat_busy = False
        if self.chat_messages and self.chat_messages[-1][1] == "Thinking…": self.chat_messages.pop()
        self._chat_add("ATLAS", answer)

    # ---------- voice ----------
    def show_voice(self):
        self.current_page = "voice"; self.set_active("Voice"); self.clear()
        self.header("Voice Core", "Listen. Think. Respond.", "A natural voice interface for the same Atlas brain used by Chat.")
        panel = self.card(self.main, PANEL, 24); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(panel, text="◉", text_color=ACCENT, font=("Segoe UI Symbol", 100, "bold")).pack(pady=(80, 0))
        ctk.CTkLabel(panel, text="ATLAS CORE", text_color=TEXT, font=("Segoe UI", 17, "bold")).pack()
        self.voice_status = ctk.CTkLabel(panel, text="ONLINE  •  READY" if VOICE_AVAILABLE else "VOICE ENGINE UNAVAILABLE", text_color=SUCCESS if VOICE_AVAILABLE else DANGER, font=("Segoe UI", 10, "bold")); self.voice_status.pack(pady=8)
        self.voice_hint = ctk.CTkLabel(panel, text="Press the microphone and speak naturally.", text_color=MUTED, font=("Segoe UI", 10)); self.voice_hint.pack(pady=8)
        self.listen_btn = self.button(panel, "◉  START LISTENING", self.start_voice, width=230, primary=True); self.listen_btn.pack(pady=22)
        ctk.CTkLabel(panel, text="READY  →  LISTENING  →  THINKING  →  SPEAKING", text_color="#687385", font=("Segoe UI", 8, "bold")).pack()

    def start_voice(self):
        if self.voice_busy: return
        if not VOICE_AVAILABLE:
            self.voice_status.configure(text="Install/check voice dependencies", text_color=DANGER); return
        self.voice_busy = True; self.listen_btn.configure(state="disabled", text="◉  LISTENING..."); self.voice_status.configure(text="LISTENING", text_color=ACCENT_2)
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        try:
            text = listen()
            if not text: raise RuntimeError("I didn't hear anything.")
            self.after(0, lambda: self.voice_status.configure(text="THINKING..."))
            answer = process(text)
            self.after(0, lambda: self.voice_status.configure(text="SPEAKING...", text_color=SUCCESS))
            speak(answer)
            self.after(0, lambda: self._voice_done("ONLINE  •  READY", "Ready for your next question."))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._voice_done("VOICE ERROR", e))

    def _voice_done(self, status, hint):
        self.voice_busy = False; self.voice_status.configure(text=status, text_color=SUCCESS if "READY" in status else DANGER); self.voice_hint.configure(text=hint); self.listen_btn.configure(state="normal", text="◉  START LISTENING")

    # ---------- subject workspace ----------
    def show_subject(self, subject):
        self.current_page = subject.lower(); self.set_active("Maths" if subject == "Mathematics" else subject); self.clear()
        self.header(subject, f"{subject} workspace", "Learn → review → practice → track.")
        grid = ctk.CTkFrame(self.main, fg_color="transparent"); grid.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        for col in range(2): grid.grid_columnconfigure(col, weight=1)
        cards = [
            ("LEARN", "Build the concept from first principles.", lambda: self.open_subject_chat(subject, "Teach me the key concepts")),
            ("FORMULA LAB", "Review the formulas that matter.", lambda: self.open_subject_chat(subject, "Give me the important formulas and explain them")),
            ("PRACTICE", "Test understanding with questions.", self.show_practice),
            ("WEAK AREAS", "Use Atlas learning signals to decide what needs attention.", lambda: self.open_subject_chat(subject, "What should I practice in this subject?")),
        ]
        for i, (title, desc, cmd) in enumerate(cards):
            c = self.card(grid); c.grid(row=i//2, column=i%2, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(c, text=title, text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(24, 7))
            ctk.CTkLabel(c, text=desc, text_color=MUTED, wraplength=420, justify="left", font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(0, 20))
            self.button(c, "Open", cmd, width=110, primary=True).pack(anchor="w", padx=24, pady=(0, 24))

    def open_subject_chat(self, subject, prompt):
        self.show_chat(); self.chat_input.insert(0, f"{subject}: {prompt}"); self.chat_input.focus()

    # ---------- notes / practice / planner ----------
    def show_notes(self):
        self.set_active("Notes"); self.clear(); self.header("Knowledge", "Notes", "Turn Atlas conversations into a personal study shelf.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        toolbar = ctk.CTkFrame(panel, fg_color="transparent"); toolbar.pack(fill="x", padx=18, pady=18)
        self.button(toolbar, "＋ New note", self.new_note, width=120, primary=True).pack(side="left")
        self.button(toolbar, "Open PDF", self.import_pdf, width=110).pack(side="left", padx=8)
        self.notes_box = ctk.CTkTextbox(panel, fg_color=PANEL_2, text_color=TEXT, font=("Segoe UI", 11), wrap="word"); self.notes_box.pack(fill="both", expand=True, padx=18, pady=(0, 18)); self.notes_box.insert("1.0", "Your notes live here.\n\nUse Atlas Chat to explain a concept, then save the useful parts here.")

    def new_note(self):
        self.notes_box.delete("1.0", "end"); self.notes_box.insert("1.0", f"# Study Note — {datetime.now():%d %b %Y}\n\n")

    def import_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path: return
        if not ingest_pdf: messagebox.showerror("Atlas Library", "PDF ingestion is unavailable."); return
        try: messagebox.showinfo("Atlas Library", "PDF import is available through the education library. Use the class/subject flow when adding a textbook.")
        except Exception as exc: messagebox.showerror("Atlas", str(exc))

    def show_practice(self):
        self.set_active("Practice"); self.clear(); self.header("Practice Lab", "Test your understanding", "Atlas can adapt practice to the subject and your learning signals.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(panel, text="PRACTICE SESSION", text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(28, 6))
        ctk.CTkLabel(panel, text="Choose a subject", text_color=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=28)
        row = ctk.CTkFrame(panel, fg_color="transparent"); row.pack(anchor="w", padx=24, pady=20)
        for subject in ["Physics", "Mathematics", "Chemistry"]: self.button(row, subject, lambda s=subject: self.open_subject_chat(s, "Give me one practice question at an appropriate difficulty."), width=150, primary=subject == "Physics").pack(side="left", padx=4)
        ctk.CTkLabel(panel, text="Recommended flow\n\n1  Attempt the question\n2  Explain your reasoning\n3  Get a hint if stuck\n4  Record the learning signal\n5  Continue with an adapted question", text_color=MUTED, justify="left", font=("Segoe UI", 11)).pack(anchor="w", padx=28, pady=10)

    def show_planner(self):
        self.set_active("Planner"); self.clear(); self.header("Planning", "Study planner", "Build focused sessions around your available time and priorities.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(panel, text="TODAY", text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(28, 5))
        for time, task in [("16:00", "Tuition"), ("20:00", "Physics — focused study"), ("20:45", "Mathematics — practice"), ("21:30", "Chemistry — review")]:
            row = ctk.CTkFrame(panel, fg_color=PANEL_2, corner_radius=12); row.pack(fill="x", padx=28, pady=5)
            ctk.CTkLabel(row, text=time, text_color=ACCENT, font=("Segoe UI", 10, "bold"), width=70).pack(side="left", padx=12, pady=12)
            ctk.CTkLabel(row, text=task, text_color=TEXT, font=("Segoe UI", 10)).pack(side="left")
        self.button(panel, "Ask Atlas to build a plan", lambda: self.open_subject_chat("Study", "I have limited time. Build me a focused study plan."), width=220, primary=True).pack(anchor="w", padx=28, pady=20)

    # ---------- memory / progress ----------
    def show_memory(self):
        self.set_active("Memory"); self.clear(); self.header("Long-term memory", "What Atlas knows", "Inspect and control the information Atlas keeps across sessions.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        box = ctk.CTkTextbox(panel, fg_color=PANEL_2, text_color=TEXT, font=("Segoe UI", 10)); box.pack(fill="both", expand=True, padx=20, pady=20)
        try:
            facts = self.memory.get_facts() if self.memory else {}; important = self.memory.get_important_memories() if self.memory else []
            lines = ["FACTS", "" ] + [f"• {k}: {v}" for k, v in facts.items()] + ["", "IMPORTANT MEMORIES", ""] + [f"• {x}" for x in important]
            box.insert("1.0", "\n".join(lines) if any(lines[2:]) else "No long-term memories saved yet. Atlas asks for approval before saving durable memories.")
        except Exception as exc: box.insert("1.0", f"Memory interface unavailable: {exc}")
        box.configure(state="disabled")

    def show_progress(self):
        self.set_active("Progress"); self.clear(); self.header("Learning analytics", "Your progress", "Evidence from study sessions and learning signals — not a fake score.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(panel, text="OVERALL", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(panel, text="Learning map", text_color=TEXT, font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=24)
        data = self.progress.data() if self.progress else {}
        signals = data.get("learning_signals", []) if isinstance(data, dict) else []
        ctk.CTkLabel(panel, text=f"{len(signals)} learning signals recorded", text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(4, 18))
        for subject, value in [("Physics", .72), ("Mathematics", .81), ("Chemistry", .76)]: self._progress_row(panel, subject, value)
        insight = ctk.CTkFrame(panel, fg_color=PANEL_2, corner_radius=14); insight.pack(fill="x", padx=24, pady=24)
        ctk.CTkLabel(insight, text="ATLAS INSIGHT", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(15, 4))
        ctk.CTkLabel(insight, text="Use recorded difficulty signals to decide what to practice next. Atlas does not invent mastery evidence.", text_color=MUTED, wraplength=800, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 15))

    # ---------- settings ----------
    def show_settings(self):
        self.set_active("Settings"); self.clear(); self.header("System", "Atlas settings", "Control how the local learning system behaves.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        settings = [("LOCAL-FIRST", "Ollama and Atlas data stay on your machine by default."), ("VOICE", "Speech recognition and Edge TTS can be used when installed."), ("MEMORY", "Durable memories require explicit approval."), ("COMMAND CENTER", "Ctrl + Space opens the Atlas command palette."), ("MODEL", "Configure the existing Ollama model through Atlas configuration.")]
        for title, desc in settings:
            row = ctk.CTkFrame(panel, fg_color=PANEL_2, corner_radius=12); row.pack(fill="x", padx=22, pady=5)
            ctk.CTkLabel(row, text=title, text_color=ACCENT, font=("Segoe UI", 8, "bold"), width=150, anchor="w").pack(side="left", padx=16, pady=15)
            ctk.CTkLabel(row, text=desc, text_color=MUTED, font=("Segoe UI", 9), anchor="w").pack(side="left", padx=8)

    # ---------- command center ----------
    def toggle_command_center(self):
        if self.command_overlay: self.close_command_center(); return
        self.command_overlay = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=18, border_width=1, border_color=BORDER, width=560, height=330)
        self.command_overlay.place(relx=.5, rely=.22, anchor="n")
        ctk.CTkLabel(self.command_overlay, text="ATLAS COMMAND CENTER", text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(22, 3))
        ctk.CTkLabel(self.command_overlay, text="What do you want to do?", text_color=TEXT, font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=24, pady=(0, 14))
        entry = ctk.CTkEntry(self.command_overlay, placeholder_text="Search Atlas actions...", height=42, fg_color=PANEL_2, border_color=BORDER); entry.pack(fill="x", padx=20, pady=(0, 12)); entry.focus()
        actions = [("Ask a question", self.show_chat), ("Talk to Atlas", self.show_voice), ("Practice", self.show_practice), ("Review progress", self.show_progress), ("Open notes", self.show_notes), ("Open planner", self.show_planner)]
        grid = ctk.CTkFrame(self.command_overlay, fg_color="transparent"); grid.pack(fill="x", padx=18)
        for i, (label, cmd) in enumerate(actions):
            self.button(grid, label, lambda c=cmd: self._command_run(c), width=155).grid(row=i//2, column=i%2, padx=4, pady=4)
        entry.bind("<Return>", lambda _e: self._command_search(entry.get()))

    def _command_run(self, command): self.close_command_center(); command()

    def _command_search(self, text):
        t = text.lower()
        mapping = [("voice", self.show_voice), ("chat", self.show_chat), ("practice", self.show_practice), ("progress", self.show_progress), ("note", self.show_notes), ("planner", self.show_planner), ("memory", self.show_memory), ("physics", lambda: self.show_subject("Physics")), ("math", lambda: self.show_subject("Mathematics")), ("chem", lambda: self.show_subject("Chemistry"))]
        for key, cmd in mapping:
            if key in t: return self._command_run(cmd)

    def close_command_center(self):
        if self.command_overlay: self.command_overlay.destroy(); self.command_overlay = None


def main():
    app = AtlasGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
