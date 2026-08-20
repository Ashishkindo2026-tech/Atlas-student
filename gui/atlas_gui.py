"""Atlas Student desktop GUI.

Thin, responsive presentation layer. Intelligence, voice, education and
persistence stay delegated to their existing services.
"""
import os
import sys
import threading
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from brain.agent import process
from education.ingest import ingest_pdf

try:
    from voice.voice_engine import listen, speak
    VOICE_AVAILABLE = True
except Exception:
    listen = speak = None
    VOICE_AVAILABLE = False

BG = "#090B10"
SURFACE = "#10141C"
SURFACE_2 = "#151A24"
TEXT = "#F3F5F7"
MUTED = "#8D97A8"
ACCENT = "#7C9CFF"
ACCENT_HOVER = "#9CB4FF"
ACCENT_SOFT = "#263252"
SUCCESS = "#6FD1A5"
DANGER = "#E58C8C"
BORDER = "#252D3B"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AtlasGUI(ctk.CTk):
    """Responsive Atlas shell with safe service boundaries."""

    def __init__(self):
        super().__init__()
        self.title("Atlas Student")
        self.geometry("1320x820")
        self.minsize(1050, 680)
        self.configure(fg_color=BG)
        self.voice_busy = False
        self.service_busy = False
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Control-q>", lambda _event: self._close())
        self._build_shell()
        self.show_home()

    def _build_shell(self):
        self.rail = ctk.CTkFrame(self, width=82, fg_color="#07090D", corner_radius=0)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)
        ctk.CTkLabel(self.rail, text="A", text_color=ACCENT,
                     font=("Georgia", 28, "bold")).pack(pady=(28, 4))
        ctk.CTkLabel(self.rail, text="ATLAS", text_color=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(pady=(0, 28))
        for icon, command in [
            ("⌂", self.show_home), ("◉", self.show_voice),
            ("▱", self.show_library), ("◌", self.show_memory),
            ("◇", self.show_goals), ("▥", self.show_progress),
        ]:
            ctk.CTkButton(
                self.rail, text=icon, command=command, width=54, height=48,
                fg_color="transparent", hover_color=ACCENT_SOFT,
                text_color=MUTED, font=("Segoe UI Symbol", 19), corner_radius=14,
            ).pack(pady=4)
        ctk.CTkButton(
            self.rail, text="⚙", command=self.show_settings, width=54, height=42,
            fg_color="transparent", hover_color=SURFACE_2, text_color=MUTED,
            font=("Segoe UI", 16), corner_radius=12,
        ).pack(side="bottom", pady=20)
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, eyebrow, title, subtitle=""):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=46, pady=(34, 0))
        ctk.CTkLabel(top, text=eyebrow.upper(), text_color=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ctk.CTkLabel(top, text=title, text_color=TEXT,
                     font=("Georgia", 31, "bold")).pack(anchor="w", pady=(4, 0))
        if subtitle:
            ctk.CTkLabel(top, text=subtitle, text_color=MUTED,
                         font=("Segoe UI", 11), wraplength=900,
                         justify="left").pack(anchor="w", pady=(4, 20))

    def surface(self, parent=None, color=SURFACE, radius=18):
        return ctk.CTkFrame(parent or self.main, fg_color=color,
                            corner_radius=radius, border_width=1,
                            border_color=BORDER)

    def _run_background(self, work, success, failure):
        """Execute service work off the Tk thread and marshal results back."""
        if self.service_busy:
            return False
        self.service_busy = True

        def worker():
            try:
                result = work()
            except Exception as exc:
                self.after(0, lambda e=str(exc): failure(e))
            else:
                self.after(0, lambda r=result: success(r))
            finally:
                self.after(0, self._clear_service_busy)

        threading.Thread(target=worker, daemon=True, name="atlas-service").start()
        return True

    def _clear_service_busy(self):
        self.service_busy = False

    def show_home(self):
        self.clear()
        self.header("Atlas Student", "Your learning orbit.",
                    "Books, memory, goals, progress and voice in one local-first interface.")
        body = ctk.CTkFrame(self.main, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=46, pady=(0, 36))
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure((0, 1), weight=1)
        focus = self.surface(body, SURFACE, 24)
        focus.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 14))
        status = "VOICE READY" if VOICE_AVAILABLE else "VOICE UNAVAILABLE"
        ctk.CTkLabel(focus, text=status,
                     text_color=SUCCESS if VOICE_AVAILABLE else DANGER,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=28, pady=(26, 0))
        ctk.CTkLabel(focus, text="Atlas Student\nready to learn.", text_color=TEXT,
                     justify="left", font=("Georgia", 34, "bold")).pack(anchor="w", padx=28, pady=(8, 8))
        ctk.CTkLabel(focus,
                     text="Use Atlas's existing brain for study questions, planning,\nmemory and learning support.",
                     text_color=MUTED, justify="left", font=("Segoe UI", 11)).pack(anchor="w", padx=28)
        ctk.CTkButton(focus, text="◉  Open Voice", command=self.show_voice,
                      width=220, height=52, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color=BG,
                      font=("Segoe UI", 12, "bold"), corner_radius=16).pack(anchor="w", padx=28, pady=(30, 14))
        self._card(body, 0, 1, "MEMORY", "Persistent local memory", "Inspectable and recoverable.")
        self._card(body, 1, 1, "LEARNING", "Student intelligence", "Goals, planning and progress stay connected.")

    def _card(self, parent, row, col, title, heading, body):
        card = self.surface(parent, SURFACE_2, 20)
        card.grid(row=row, column=col, sticky="nsew", pady=7)
        ctk.CTkLabel(card, text=title, text_color=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(card, text=heading, text_color=TEXT,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(card, text=body, text_color=MUTED, wraplength=300,
                     justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(5, 16))

    def show_voice(self):
        self.clear()
        self.header("Voice", "Listen. Think. Respond.",
                    "Voice runs outside the UI thread so the window remains responsive.")
        panel = self.surface(self.main, SURFACE, 24)
        panel.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(panel, text="A", text_color=ACCENT,
                     font=("Georgia", 88, "bold")).pack(pady=(70, 0))
        ctk.CTkLabel(panel, text="ATLAS", text_color=TEXT,
                     font=("Segoe UI", 16, "bold")).pack()
        self.voice_status = ctk.CTkLabel(
            panel, text="Ready to listen" if VOICE_AVAILABLE else "Voice engine unavailable",
            text_color=SUCCESS if VOICE_AVAILABLE else DANGER,
            font=("Segoe UI", 11, "bold"))
        self.voice_status.pack(pady=8)
        self.voice_hint = ctk.CTkLabel(panel, text="Press the microphone and speak.",
                                       text_color=MUTED, font=("Segoe UI", 10))
        self.voice_hint.pack(pady=(0, 20))
        self.listen_button = ctk.CTkButton(
            panel, text="◉  START LISTENING", command=self.start_voice,
            width=230, height=54, fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=BG, font=("Segoe UI", 11, "bold"), corner_radius=17,
            state="normal" if VOICE_AVAILABLE else "disabled")
        self.listen_button.pack(pady=10)

    def start_voice(self):
        if self.voice_busy or not VOICE_AVAILABLE:
            return
        self.voice_busy = True
        self.listen_button.configure(state="disabled", text="◉  LISTENING...",
                                      fg_color=ACCENT_SOFT, text_color=TEXT)
        self.voice_status.configure(text="Listening...", text_color=ACCENT_HOVER)
        threading.Thread(target=self._voice_worker, daemon=True, name="atlas-voice").start()

    def _voice_worker(self):
        try:
            text = listen()
            if not text:
                self.after(0, lambda: self._voice_finished("I didn't hear anything. Try again."))
                return
            self.after(0, lambda: self.voice_status.configure(text="Thinking...", text_color=ACCENT_HOVER))
            answer = process(text)
            if answer:
                speak(answer)
            self.after(0, lambda: self._voice_finished("Ready to listen"))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._voice_finished(f"Voice error: {e}"))

    def _voice_finished(self, status):
        self.voice_busy = False
        if not self.winfo_exists() or not hasattr(self, "voice_status"):
            return
        ok = status == "Ready to listen"
        self.voice_status.configure(text=status, text_color=SUCCESS if ok else DANGER)
        self.listen_button.configure(state="normal" if VOICE_AVAILABLE else "disabled",
                                     text="◉  START LISTENING", fg_color=ACCENT,
                                     text_color=BG)

    def show_library(self):
        self.clear()
        self.header("NCERT Library", "Your study shelf.",
                    "Add authorized PDFs and index them through the existing education service.")
        ctk.CTkButton(self.main, text="＋ Add PDF", command=self.add_book, height=40,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=BG).pack(anchor="w", padx=46, pady=(0, 15))
        grid = ctk.CTkFrame(self.main, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1)
        books = [("9", "Science"), ("9", "Mathematics"), ("10", "Science"),
                 ("10", "Mathematics"), ("11", "Physics"), ("11", "Chemistry"),
                 ("11", "Mathematics"), ("12", "Physics"), ("12", "Chemistry"),
                 ("12", "Mathematics"), ("12", "Biology")]
        for i, (grade, subject) in enumerate(books):
            self._card(grid, i // 4, i % 4, f"CLASS {grade}", subject, "Core study library")

    def add_book(self):
        if self.service_busy:
            return
        path = filedialog.askopenfilename(title="Choose an authorized textbook PDF",
                                          filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        level = simpledialog.askinteger("Class", "Class (9–12):", minvalue=9, maxvalue=12, parent=self)
        subject = simpledialog.askstring("Subject", "Subject:", parent=self) if level else None
        if not level or not subject:
            return
        self._run_background(
            lambda: ingest_pdf(path, level, subject),
            lambda data: messagebox.showinfo("Atlas Library",
                f"Indexed: {data.get('title', os.path.basename(path))}\nPages: {data.get('pages_indexed', 0)}"),
            lambda error: messagebox.showerror("Import failed", error),
        )

    def show_memory(self):
        self.clear()
        self.header("Memory", "What Atlas knows.",
                    "Memory remains separate from the interface and can be controlled by the memory service.")
        for title, body in [("IDENTITY", "Stored facts and identity information."),
                            ("IMPORTANT", "User-approved important memories."),
                            ("LEARNING", "Topics, difficulty signals and progress evidence."),
                            ("RECOVERY", "Atomic writes, corruption recovery and archive support.")]:
            card = self.surface(self.main, SURFACE, 18)
            card.pack(fill="x", padx=46, pady=6)
            ctk.CTkLabel(card, text=title, text_color=ACCENT,
                         font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=22, pady=(16, 5))
            ctk.CTkLabel(card, text=body, text_color=TEXT,
                         font=("Segoe UI", 11)).pack(anchor="w", padx=22, pady=(0, 16))

    def show_goals(self):
        self.clear()
        self.header("Goals", "Direction, not pressure.",
                    "Goals are handled by Atlas's student-intelligence layer.")
        for title, body in [("Build Atlas Student", "Core AI, memory and reliability work."),
                            ("Strengthen Physics", "Concept practice, revision and evidence-based progress.")]:
            card = self.surface(self.main, SURFACE, 18)
            card.pack(fill="x", padx=46, pady=6)
            ctk.CTkLabel(card, text="ACTIVE", text_color=SUCCESS,
                         font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
            ctk.CTkLabel(card, text=title, text_color=TEXT,
                         font=("Georgia", 18, "bold")).pack(anchor="w", padx=22)
            ctk.CTkLabel(card, text=body, text_color=MUTED,
                         font=("Segoe UI", 10)).pack(anchor="w", padx=22, pady=(4, 18))

    def show_progress(self):
        self.clear()
        self.header("Progress", "Your learning map.",
                    "Progress should come from evidence, not hard-coded claims.")
        card = self.surface(self.main, SURFACE, 20)
        card.pack(fill="both", expand=True, padx=46, pady=(0, 30))
        ctk.CTkLabel(card, text="Atlas learning progress is maintained by the student-intelligence system.",
                     text_color=MUTED, wraplength=700, justify="left",
                     font=("Segoe UI", 11)).pack(anchor="w", padx=28, pady=28)

    def show_settings(self):
        self.clear()
        self.header("Settings", "Make Atlas yours.",
                    "Local-first settings and future personalization controls.")
        card = self.surface(self.main, SURFACE, 20)
        card.pack(fill="x", padx=46, pady=(0, 12))
        ctk.CTkLabel(card, text="Interface", text_color=TEXT,
                     font=("Georgia", 17, "bold")).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(card, text=f"Voice engine: {'available' if VOICE_AVAILABLE else 'unavailable'}",
                     text_color=SUCCESS if VOICE_AVAILABLE else DANGER,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=24, pady=(0, 8))
        ctk.CTkLabel(card,
                     text="Atlas keeps the UI responsive by moving voice and PDF indexing work to background threads and routing services through dedicated modules.",
                     text_color=MUTED, wraplength=800, justify="left",
                     font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(0, 22))

    def _close(self):
        self.voice_busy = False
        self.destroy()


if __name__ == "__main__":
    AtlasGUI().mainloop()
