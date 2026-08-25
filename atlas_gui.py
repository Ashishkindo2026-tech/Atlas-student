"""ATLAS — Personal AI Learning System desktop dashboard.

Standard-library Tkinter UI so the dashboard can run without a web stack.
The visual language is intentionally different from chat-first AI products:
learning modes, progress, subjects, and Atlas Core status are the primary UI.
"""
from __future__ import annotations

import tkinter as tk
from datetime import datetime

from brain.agent import process
from student.atlas_student import system

BG = "#0b0f14"
PANEL = "#111720"
PANEL_2 = "#151d27"
BORDER = "#26313d"
TEXT = "#eef3f8"
MUTED = "#8e9aa8"
ACCENT = "#79d8c5"
ACCENT_DARK = "#173b3a"


class AtlasDashboard(tk.Tk):
    """Premium desktop dashboard for Atlas Student."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ATLAS — Your learning system")
        self.geometry("1180x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.option_add("*Font", ("Segoe UI", 10))
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
        card = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1, width=220, height=135, cursor="hand2")
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        card.pack_propagate(False)
        self._label(card, icon, 22, color=ACCENT).pack(anchor="w", padx=18, pady=(16, 4))
        self._label(card, title, 11, "bold").pack(anchor="w", padx=18)
        self._label(card, desc, 9, color=MUTED, wraplength=190, justify="left").pack(anchor="w", padx=18, pady=(5, 0))
        for widget in (card,):
            widget.bind("<Button-1>", lambda e, fn=command: fn())
            widget.bind("<Enter>", lambda e, w=widget: w.configure(bg=PANEL_2))
            widget.bind("<Leave>", lambda e, w=widget: w.configure(bg=PANEL))

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


if __name__ == "__main__":
    AtlasDashboard().mainloop()
