import os
import sys
import threading
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.agent import process
from education.ingest import ingest_pdf

try:
    from voice.voice_engine import listen, speak
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

        nav = [("⌂", self.show_home), ("◉", self.show_voice), ("▱", self.show_library), ("◌", self.show_memory), ("◇", self.show_goals), ("▥", self.show_progress)]
        for icon, command in nav:
            ctk.CTkButton(self.rail, text=icon, command=command, width=54, height=48, fg_color="transparent", hover_color=ACCENT_SOFT, text_color=MUTED, font=("Segoe UI Symbol", 19), corner_radius=14).pack(pady=4)

        ctk.CTkButton(self.rail, text="⚙", command=self.show_settings, width=54, height=42, fg_color="transparent", hover_color=SURFACE_2, text_color=MUTED, font=("Segoe UI", 16), corner_radius=12).pack(side="bottom", pady=20)
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
