import os
import sys
import threading
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.agent import process
from education.ingest import ingest_pdf

try:
    from voice_engine import listen, speak
    VOICE_AVAILABLE = True
except Exception:
    listen = None
    speak = None
    VOICE_AVAILABLE = False


# Atlas Student — Orbit Voice UI
# Voice-first interface: Atlas is spoken to, not typed to.
BG = "#090B10"
SURFACE = "#10141C"
SURFACE_2 = "#151A24"
SURFACE_3 = "#1B2130"
TEXT = "#F3F5F7"
MUTED = "#8D97A8"
ACCENT = "#7C9CFF"
ACCENT_HOVER = "#9CB4FF"
ACCENT_SOFT = "#263252"
SUCCESS = "#6FD1A5"
BORDER = "#252D3B"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AtlasGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atlas Student")
        self.geometry("1320x820")
        self.minsize(1050, 680)
        self.configure(fg_color=BG)
        self.voice_busy = False
        self.current_page = "home"
        self._build_shell()
        self.show_home()

    # ---------------------------- shell ----------------------------

    def _build_shell(self):
        self.rail = ctk.CTkFrame(self, width=82, fg_color="#07090D", corner_radius=0)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        ctk.CTkLabel(self.rail, text="A", text_color=ACCENT, font=("Georgia", 28, "bold")).pack(pady=(28, 4))
        ctk.CTkLabel(self.rail, text="ATLAS", text_color=MUTED, font=("Segoe UI", 8, "bold")).pack(pady=(0, 28))

        nav = [
            ("⌂", self.show_home),
            ("◉", self.show_voice),
            ("▱", self.show_library),
            ("◌", self.show_memory),
            ("◇", self.show_goals),
            ("▥", self.show_progress),
        ]
        for icon, command in nav:
            ctk.CTkButton(
                self.rail, text=icon, command=command,
                width=54, height=48, fg_color="transparent",
                hover_color=ACCENT_SOFT, text_color=MUTED,
                font=("Segoe UI Symbol", 19), corner_radius=14
            ).pack(pady=4)

        ctk.CTkButton(
            self.rail, text="⚙", command=self.show_settings,
            width=54, height=42, fg_color="transparent",
            hover_color=SURFACE_2, text_color=MUTED,
            font=("Segoe UI", 16), corner_radius=12
        ).pack(side="bottom", pady=20)

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, eyebrow, title, subtitle=""):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=46, pady=(34, 0))
        ctk.CTkLabel(top, text=eyebrow.upper(), text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ctk.CTkLabel(top, text=title, text_color=TEXT, font=("Georgia", 31, "bold")).pack(anchor="w", pady=(4, 0))
        if subtitle:
            ctk.CTkLabel(top, text=subtitle, text_color=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 20))

    def surface(self, parent=None, color=SURFACE, radius=18):
        return ctk.CTkFrame(parent or self.main, fg_color=color, corner_radius=radius, border_width=1, border_color=BORDER)

    def pill(self, parent, text, command=None):
        return ctk.CTkButton(parent, text=text, command=command, height=30, corner_radius=15, fg_color=SURFACE_2, hover_color=SURFACE_3, text_color=MUTED, font=("Segoe UI", 9, "bold"))

    # ---------------------------- home ----------------------------

    def show_home(self):
        self.current_page = "home"
        self.clear()
        self.header("Atlas Student", "Your learning orbit.", "Talk to Atlas. Your books, memory, goals and progress stay connected.")

        body = ctk.CTkFrame(self.main, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=46, pady=(0, 36))
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        focus = self.surface(body, SURFACE, 24)
        focus.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))
        ctk.CTkLabel(focus, text="VOICE READY" if VOICE_AVAILABLE else "VOICE ENGINE NOT FOUND", text_color=SUCCESS if VOICE_AVAILABLE else "#E58C8C", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(26, 0))
        ctk.CTkLabel(focus, text="Talk to Atlas.\nNo typing needed.", text_color=TEXT, justify="left", font=("Georgia", 34, "bold")).pack(anchor="w", padx=28, pady=(8, 8))
        ctk.CTkLabel(focus, text="Press the microphone, speak naturally, and Atlas will\nlisten, think with its existing brain, and answer aloud.", text_color=MUTED, justify="left", font=("Segoe UI", 11)).pack(anchor="w", padx=28)

        ctk.CTkButton(focus, text="◉  Talk to Atlas", command=self.show_voice, width=220, height=52, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=BG, font=("Segoe UI", 12, "bold"), corner_radius=16).pack(anchor="w", padx=28, pady=(30, 14))
        self.pill(focus, "Voice-first mode", self.show_voice).pack(anchor="w", padx=28)

        memory = self.surface(body, SURFACE_2, 20)
        memory.grid(row=0, column=1, sticky="nsew", pady=(0, 7))
        ctk.CTkLabel(memory, text="MEMORY", text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(memory, text="1 important memory", text_color=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(memory, text="You are building Atlas Student.", text_color=MUTED, wraplength=300, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(5, 16))

        progress = self.surface(body, SURFACE_2, 20)
        progress.grid(row=1, column=1, sticky="nsew", pady=(7, 0))
        ctk.CTkLabel(progress, text="LEARNING", text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(progress, text="Physics", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=20)
        bar = ctk.CTkProgressBar(progress, progress_color=ACCENT, fg_color=BORDER)
        bar.pack(fill="x", padx=20, pady=10)
        bar.set(0.60)
        ctk.CTkLabel(progress, text="Keep building your learning map.", text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=20)

    # ---------------------------- voice ----------------------------

    def show_voice(self):
        self.current_page = "voice"
        self.clear()
        self.header("Voice", "Listen. Think. Respond.", "Atlas Student is now voice-first — there is no chat box or text message input.")

        panel = self.surface(self.main, SURFACE, 24)
        panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))

        self.orb = ctk.CTkLabel(panel, text="A", text_color=ACCENT, font=("Georgia", 88, "bold"))
        self.orb.pack(pady=(85, 0))
        ctk.CTkLabel(panel, text="ATLAS", text_color=TEXT, font=("Segoe UI", 16, "bold")).pack(pady=(0, 4))

        self.voice_status = ctk.CTkLabel(panel, text="Ready to listen" if VOICE_AVAILABLE else "Voice engine unavailable", text_color=SUCCESS if VOICE_AVAILABLE else "#E58C8C", font=("Segoe UI", 11, "bold"))
        self.voice_status.pack(pady=8)

        self.voice_hint = ctk.CTkLabel(panel, text="Press the microphone and speak.", text_color=MUTED, font=("Segoe UI", 10))
        self.voice_hint.pack(pady=(0, 20))

        self.listen_button = ctk.CTkButton(panel, text="◉  START LISTENING", command=self.start_voice, width=230, height=54, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=BG, font=("Segoe UI", 11, "bold"), corner_radius=17)
        self.listen_button.pack(pady=10)

        ctk.CTkLabel(panel, text="Your speech is converted to a command for Atlas's existing brain.\nAtlas's answer is then spoken back through the voice engine.", text_color=MUTED, justify="center", font=("Segoe UI", 9)).pack(pady=18)

    def start_voice(self):
        if self.voice_busy:
            return
        if not VOICE_AVAILABLE:
            self.voice_status.configure(text="Install/check voice_engine.py dependencies", text_color="#E58C8C")
            return
        self.voice_busy = True
        self.listen_button.configure(state="disabled", text="◉  LISTENING...", fg_color=ACCENT_SOFT, text_color=TEXT)
        self.voice_status.configure(text="Listening...", text_color=ACCENT_HOVER)
        self.voice_hint.configure(text="Speak now. Atlas is listening.")
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        try:
            text = listen()
            if not text:
                self.after(0, lambda: self._voice_finished("I didn't hear anything. Try again."))
                return
            if text.startswith("error:"):
                self.after(0, lambda t=text: self._voice_finished(t))
                return
            self.after(0, lambda: self.voice_status.configure(text="Thinking...", text_color=ACCENT_HOVER))
            answer = process(text)
            self.after(0, lambda t=text: self.voice_hint.configure(text="Heard you. Atlas is responding aloud."))
            speak(answer)
            self.after(0, lambda: self._voice_finished("Ready to listen"))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._voice_finished(f"Voice error: {e}"))

    def _voice_finished(self, status):
        self.voice_busy = False
        self.voice_status.configure(text=status, text_color=SUCCESS if status == "Ready to listen" else "#E58C8C")
        self.listen_button.configure(state="normal", text="◉  START LISTENING", fg_color=ACCENT, text_color=BG)
        if status == "Ready to listen":
            self.voice_hint.configure(text="Press the microphone and speak.")

    # ---------------------------- library ----------------------------

    def show_library(self):
        self.clear()
        self.header("NCERT Library", "Your study shelf.", "Core Classes 9–12. Add authorized PDFs from your computer.")
        toolbar = ctk.CTkFrame(self.main, fg_color="transparent")
        toolbar.pack(fill="x", padx=46, pady=(0, 14))
        ctk.CTkButton(toolbar, text="＋ Add PDF", command=self.add_book, height=38, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=BG, corner_radius=12).pack(side="left")
        ctk.CTkLabel(toolbar, text="  Searchable text • page-aware indexing", text_color=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=12)
        grid = ctk.CTkFrame(self.main, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        for col in range(4): grid.grid_columnconfigure(col, weight=1)
        for row in range(3): grid.grid_rowconfigure(row, weight=1)
        subjects = [
            ("09", "Science", "Physics • Chemistry • Biology"), ("09", "Mathematics", "NCERT Mathematics"),
            ("10", "Science", "Physics • Chemistry • Biology"), ("10", "Mathematics", "NCERT Mathematics"),
            ("11", "Physics", "Core Physics"), ("11", "Chemistry", "Core Chemistry"),
            ("11", "Mathematics", "Core Mathematics"), ("12", "Physics", "Core Physics"),
            ("12", "Chemistry", "Core Chemistry"), ("12", "Mathematics", "Core Mathematics"),
            ("12", "Biology", "Core Biology"), ("09–12", "Your PDFs", "Add your own authorized books"),
        ]
        for i, (grade, subject, detail) in enumerate(subjects):
            card = self.surface(grid, SURFACE, 16)
            card.grid(row=i // 4, column=i % 4, sticky="nsew", padx=5, pady=5)
            ctk.CTkLabel(card, text=f"CLASS {grade}", text_color=ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
            ctk.CTkLabel(card, text=subject, text_color=TEXT, font=("Georgia", 15, "bold")).pack(anchor="w", padx=16)
            ctk.CTkLabel(card, text=detail, text_color=MUTED, wraplength=190, justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(6, 15))

    def add_book(self):
        path = filedialog.askopenfilename(title="Choose an authorized textbook PDF", filetypes=[("PDF files", "*.pdf")])
        if not path: return
        level = simpledialog.askinteger("Class", "Class (9–12):", minvalue=9, maxvalue=12, parent=self)
        subject = simpledialog.askstring("Subject", "Subject:", parent=self) if level else None
        if not level or not subject: return
        try:
            data = ingest_pdf(path, level, subject)
            messagebox.showinfo("Atlas Library", f"Indexed: {data['title']}\nPages: {data['pages_indexed']}")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    # ---------------------------- memory ----------------------------

    def show_memory(self):
        self.clear()
        self.header("Memory", "What Atlas knows.", "Memory is separate from voice conversations so it can be inspected and controlled.")
        grid = ctk.CTkFrame(self.main, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        grid.grid_columnconfigure(0, weight=1); grid.grid_columnconfigure(1, weight=1)
        cards = [
            ("IDENTITY", "Name\nAshish"),
            ("IMPORTANT", "I am building Atlas Student."),
            ("PREFERENCES", "Communication and learning preferences grow over time."),
            ("LEARNING", "Topics studied, progress signals and revision needs."),
        ]
        for i, (title, body) in enumerate(cards):
            card = self.surface(grid, SURFACE, 18)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(card, text=title, text_color=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(22, 8))
            ctk.CTkLabel(card, text=body, text_color=TEXT, justify="left", wraplength=420, font=("Segoe UI", 12)).pack(anchor="w", padx=22, pady=(0, 22))
        grid.grid_rowconfigure(0, weight=1); grid.grid_rowconfigure(1, weight=1)

    # ---------------------------- goals ----------------------------

    def show_goals(self):
        self.clear()
        self.header("Goals", "Direction, not pressure.", "Atlas can turn spoken conversations into goals and connect them to learning.")
        for title, body, status in [
            ("Build Atlas Student", "Continue the core AI, memory and student-learning systems.", "ACTIVE"),
            ("Strengthen Physics", "Build a stronger concept map through NCERT study and revision.", "ACTIVE"),
        ]:
            card = self.surface(self.main, SURFACE, 18)
            card.pack(fill="x", padx=46, pady=6)
            ctk.CTkLabel(card, text=status, text_color=SUCCESS, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
            ctk.CTkLabel(card, text=title, text_color=TEXT, font=("Georgia", 18, "bold")).pack(anchor="w", padx=22)
            ctk.CTkLabel(card, text=body, text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=22, pady=(4, 18))

    # ---------------------------- progress ----------------------------

    def show_progress(self):
        self.clear()
        self.header("Progress", "Your learning map.", "Progress should come from what Atlas actually sees you learn and practice.")
        card = self.surface(self.main, SURFACE, 20)
        card.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        for name, value in [("Physics", 0.60), ("Thermodynamics", 0.60), ("Waves", 0.20), ("Concept review", 0.30)]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=28, pady=(20, 0))
            ctk.CTkLabel(row, text=name, text_color=TEXT, font=("Segoe UI", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=f"{int(value * 100)}%", text_color=MUTED, font=("Segoe UI", 10)).pack(side="right")
            bar = ctk.CTkProgressBar(card, height=10, progress_color=ACCENT, fg_color=BORDER)
            bar.pack(fill="x", padx=28, pady=(8, 0)); bar.set(value)

    # ---------------------------- settings ----------------------------

    def show_settings(self):
        self.clear()
        self.header("Settings", "Make Atlas yours.", "Voice-first interface settings and future personalization controls.")
        card = self.surface(self.main, SURFACE, 20)
        card.pack(fill="x", padx=46, pady=(0, 12))
        ctk.CTkLabel(card, text="Interface", text_color=TEXT, font=("Georgia", 17, "bold")).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(card, text="Orbit UI • Voice-first mode", text_color=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(0, 18))
        ctk.CTkLabel(card, text="Text chat input has been removed. Atlas Student is designed to be spoken to through the microphone and to answer through the voice engine.", text_color=MUTED, wraplength=700, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(0, 22))


if __name__ == "__main__":
    AtlasGUI().mainloop()
