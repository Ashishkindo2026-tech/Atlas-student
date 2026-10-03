"""Atlas Student — polished Learning OS UI.

The UI is deliberately visual-first: large hierarchy, generous spacing, soft
surfaces, a living background, clear primary actions and a real Studio preview.
Learning/voice/memory integrations remain behind the presentation layer.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog

import customtkinter as ctk
import tkinter as tk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.agent import process
from .theme_store import DEFAULT_UI as CANONICAL_UI, load_ui as load_theme, save_ui as save_theme, export_theme, import_theme
from student.learning_system import LearningSystem
from student.growth_system import GrowthSystem
from education.student_profile import EducationProfile
from atlas_core.backup import export_bundle as export_backup, restore_bundle

try:
    from voice_engine import listen, speak, stop_speaking
    VOICE_AVAILABLE = True
except Exception:
    listen = speak = stop_speaking = None
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

DEFAULT_UI = CANONICAL_UI

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
UI_FILE = APPDATA / "ui.json"
FIRST_USE_FILE = APPDATA / "first_use.json"


def load_ui():
    return load_theme()


def save_ui(data):
    return save_theme(data)


def days_used():
    """Return days since Atlas was first launched, creating the marker once."""
    try:
        APPDATA.mkdir(parents=True, exist_ok=True)
        if not FIRST_USE_FILE.exists():
            FIRST_USE_FILE.write_text(json.dumps({"first_use": time.time()}), encoding="utf-8")
        raw = json.loads(FIRST_USE_FILE.read_text(encoding="utf-8"))
        return max(0, int((time.time() - float(raw["first_use"])) / 86400))
    except Exception:
        return 0


class AtlasGUI(ctk.CTk):
    """Atlas Student Learning OS with a visual-first interface."""

    def __init__(self):
        super().__init__()
        self.ui = load_ui()
        self.days_used = days_used()
        self.title("ATLAS — Student Learning OS")
        self.geometry("1480x920")
        self.minsize(1080, 700)
        self.current_page = "home"
        self.voice_busy = False
        self.chat_busy = False
        self.command_overlay = None
        self.chat_messages: list[tuple[str, str]] = []
        self.progress = ProgressManager() if ProgressManager else None
        self.memory = MemoryManager() if MemoryManager else None
        self.learning = LearningSystem()
        self.growth = GrowthSystem()
        self.education_profile = EducationProfile()
        self._particles = []
        self._apply_window()
        self._build_shell()
        self.bind("<Control-space>", lambda _e: self.toggle_command_center())
        self.bind("<Escape>", lambda _e: self.close_command_center())
        self.show_home()
        self.after(120, self._animate_background)

    def _apply_window(self):
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.ui["background"])
        try:
            self.attributes("-alpha", float(self.ui["opacity"]))
        except Exception:
            pass

    def _c(self, key):
        return self.ui[key]

    def _font(self, size=None, weight="normal"):
        size = size or self.ui["font_size"]
        return (self.ui["font"], max(7, int(size * self.ui["ui_scale"])), weight)

    def _build_shell(self):
        for name in ("rail", "stage", "bg_canvas"):
            old = getattr(self, name, None)
            if old is not None:
                old.destroy()

        self.bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self._c("background"))
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._draw_background()

        self.stage = ctk.CTkFrame(self, fg_color="transparent")
        self.stage.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.rail = ctk.CTkFrame(self.stage, width=int(self.ui["sidebar_width"]), fg_color=self._c("sidebar"), corner_radius=0)
        if self.ui["show_sidebar"]:
            self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        brand = ctk.CTkFrame(self.rail, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(25, 18))
        orb = ctk.CTkLabel(brand, text="✦", text_color=self._c("accent"), font=("Segoe UI Symbol", 30, "bold"))
        orb.pack(side="left")
        words = ctk.CTkFrame(brand, fg_color="transparent")
        words.pack(side="left", padx=11)
        ctk.CTkLabel(words, text="ATLAS", text_color=self._c("text"), font=self._font(18, "bold")).pack(anchor="w")
        ctk.CTkLabel(words, text="STUDENT OS", text_color=self._c("muted"), font=self._font(8, "bold")).pack(anchor="w")

        if self.ui["show_status"]:
            status = ctk.CTkFrame(self.rail, fg_color=self._c("surface"), corner_radius=16)
            status.pack(fill="x", padx=15, pady=(0, 18))
            ctk.CTkLabel(status, text="●", text_color=self._c("success"), font=self._font(11)).pack(side="left", padx=(12, 7), pady=11)
            ctk.CTkLabel(status, text="CORE ONLINE", text_color=self._c("text"), font=self._font(9, "bold")).pack(side="left")
            ctk.CTkLabel(status, text="LOCAL", text_color=self._c("muted"), font=self._font(7, "bold")).pack(side="right", padx=12)

        self.nav_buttons = {}
        groups = [
            ("YOUR ATLAS", [("⌂", "Home", self.show_home), ("◈", "Chat", self.show_chat), ("◉", "Voice", self.show_voice)]),
            ("LEARNING", [("Φ", "Physics", lambda: self.show_subject("Physics")), ("∑", "Maths", lambda: self.show_subject("Mathematics")), ("⚗", "Chemistry", lambda: self.show_subject("Chemistry")), ("▣", "Notes", self.show_notes), ("◇", "Practice", self.show_practice), ("◫", "Planner", self.show_planner)]),
            ("INSIGHTS", [("◌", "Memory", self.show_memory), ("▥", "Progress", self.show_progress), ("⚙", "Settings", self.show_settings)]),
        ]
        for heading, items in groups:
            ctk.CTkLabel(self.rail, text=heading, text_color="#5F6880", font=self._font(8, "bold")).pack(anchor="w", padx=21, pady=(5, 6))
            for icon, label, command in items:
                self._nav_button(icon, label, command)

        if self.days_used >= 7:
            self._nav_button("✦", "Studio", self.show_studio, bottom=True)
        else:
            locked = self._nav_button("✦", "Studio", self.show_studio, bottom=True)
            locked.configure(text="  ✦    Studio  ·  Day 7", state="disabled", text_color="#596176")

        self.main = ctk.CTkFrame(self.stage, fg_color="transparent", corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def _draw_background(self):
        self.bg_canvas.delete("all")
        w = max(self.winfo_width(), 1200)
        h = max(self.winfo_height(), 700)
        self.bg_canvas.create_rectangle(0, 0, w, h, fill=self._c("background"), outline="")
        style = self.ui.get("background_style", "Aurora")
        if style == "Midnight":
            return
        self.bg_canvas.create_oval(w - 520, -220, w + 180, 480, fill=self._c("background_2"), outline="")
        self.bg_canvas.create_oval(-240, h - 360, 430, h + 280, fill=self._c("accent_dark" if "accent_dark" in self.ui else "background_2"), outline="")
        for i in range(24):
            x = (i * 197 + 71) % w
            y = (i * 113 + 47) % h
            r = 1 + (i % 3)
            self._particles.append(self.bg_canvas.create_oval(x-r, y-r, x+r, y+r, fill=self._c("border"), outline=""))

    def _animate_background(self):
        try:
            w = max(self.winfo_width(), 1200)
            h = max(self.winfo_height(), 700)
            for i, item in enumerate(self._particles):
                x = (i * 197 + int(time.time() * (3 + i % 3))) % w
                y = (i * 113 + 47) % h
                self.bg_canvas.coords(item, x-1, y-1, x+1, y+1)
            self.after(max(70, int(self.ui["animation_ms"])), self._animate_background)
        except tk.TclError:
            return

    def _nav_button(self, icon, label, command, bottom=False):
        b = ctk.CTkButton(self.rail, text=f"  {icon}    {label}", command=command, anchor="w", height=41,
                          fg_color="transparent", hover_color=self._c("surface_hover"), text_color=self._c("muted"),
                          corner_radius=13, font=self._font(10, "bold"))
        b.pack(side="bottom" if bottom else "top", fill="x", padx=11, pady=2)
        self.nav_buttons[label] = b
        return b

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()

    def header(self, eyebrow, title, subtitle=""):
        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.pack(fill="x", padx=45, pady=(32, 20))
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text=eyebrow.upper(), text_color=self._c("accent"), font=self._font(8, "bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=title, text_color=self._c("text"), font=self._font(self.ui["title_size"], "bold")).pack(anchor="w", pady=(2, 0))
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, text_color=self._c("muted"), font=self._font(10)).pack(anchor="w", pady=(4, 0))
        if self.ui["show_date"]:
            ctk.CTkLabel(top, text=datetime.now().strftime("%A  ·  %d %b"), text_color=self._c("muted"), font=self._font(9, "bold")).pack(side="right", anchor="n")

    def card(self, parent, color=None, radius=None, border=True):
        return ctk.CTkFrame(parent, fg_color=color or self._c("surface"), corner_radius=int(radius or self.ui["radius"]),
                            border_width=1 if border else 0, border_color=self._c("border"))

    def button(self, parent, text, command, width=145, primary=False, height=42):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
                             corner_radius=15, fg_color=self._c("accent") if primary else self._c("surface_2"),
                             hover_color=self._c("accent_2") if primary else self._c("surface_hover"),
                             text_color=self._c("background") if primary else self._c("text"), font=self._font(10, "bold"))

    def set_active(self, label):
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=self._c("surface_hover") if name == label else "transparent",
                          text_color=self._c("text") if name == label else self._c("muted"))

    def _hero(self, parent):
        hero = self.card(parent, self._c("surface"), 28)
        hero.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=30, pady=28)
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text="✦  YOUR LEARNING SPACE", text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="Learn at your pace.", text_color=self._c("text"), font=self._font(29, "bold")).pack(anchor="w", pady=(7, 3))
        ctk.CTkLabel(left, text="Atlas connects chat, voice, practice, memory and progress into one calm workspace.",
                     text_color=self._c("muted"), font=self._font(10), wraplength=600, justify="left").pack(anchor="w")
        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(anchor="w", pady=(20, 0))
        self.button(actions, "Start learning  →", self.show_chat, 170, True).pack(side="left")
        self.button(actions, "Practice", self.show_practice, 110).pack(side="left", padx=8)
        orb = ctk.CTkFrame(inner, width=145, height=145, fg_color=self._c("background_2"), corner_radius=70)
        orb.pack(side="right", padx=(20, 0)); orb.pack_propagate(False)
        ctk.CTkLabel(orb, text="✦", text_color=self._c("accent"), font=("Segoe UI Symbol", 62, "bold")).place(relx=.5, rely=.46, anchor="center")
        ctk.CTkLabel(orb, text="ATLAS", text_color=self._c("muted"), font=self._font(8, "bold")).place(relx=.5, rely=.78, anchor="center")
        return hero

    def show_home(self):
        self.set_active("Home"); self.clear(); self.header("Atlas Student", "Good to see you.", "Your next step is already here.")
        body = ctk.CTkFrame(self.main, fg_color="transparent"); body.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        self._hero(body)
        grid = ctk.CTkFrame(body, fg_color="transparent"); grid.pack(fill="both", expand=True); grid.grid_columnconfigure((0,1,2), weight=1)
        for i, (icon, title, desc, cmd) in enumerate([
            ("◈", "Chat", "Ask Atlas and learn through conversation.", self.show_chat),
            ("◉", "Voice", "Talk naturally with your Atlas teacher.", self.show_voice),
            ("◇", "Practice", "Turn weak spots into confidence.", self.show_practice),
        ]):
            c = self.card(grid); c.grid(row=0, column=i, sticky="nsew", padx=6)
            ctk.CTkLabel(c, text=icon, text_color=self._c("accent"), font=("Segoe UI Symbol", 28, "bold")).pack(anchor="w", padx=22, pady=(23, 7))
            ctk.CTkLabel(c, text=title, text_color=self._c("text"), font=self._font(17, "bold")).pack(anchor="w", padx=22)
            ctk.CTkLabel(c, text=desc, text_color=self._c("muted"), wraplength=260, justify="left", font=self._font(9)).pack(anchor="w", padx=22, pady=(5, 18))
            self.button(c, "Open", cmd, 100, title == "Chat").pack(anchor="w", padx=22, pady=(0, 22))

        bottom = self.card(body, self._c("surface"), 22)
        bottom.pack(fill="x", pady=(14, 0))
        row = ctk.CTkFrame(bottom, fg_color="transparent"); row.pack(fill="x", padx=23, pady=18)
        ctk.CTkLabel(row, text="TODAY", text_color=self._c("accent"), font=self._font(8, "bold")).pack(side="left")
        ctk.CTkLabel(row, text="  78% learning momentum", text_color=self._c("text"), font=self._font(12, "bold")).pack(side="left")
        bar = ctk.CTkProgressBar(row, height=8, progress_color=self._c("accent"), fg_color=self._c("border")); bar.pack(side="left", fill="x", expand=True, padx=25); bar.set(.78)
        ctk.CTkLabel(row, text="3 subjects active", text_color=self._c("muted"), font=self._font(9)).pack(side="right")

    def show_chat(self):
        self.set_active("Chat"); self.clear(); self.header("Atlas Core", "Talk to Atlas", "One conversation, connected to your learning system.")
        panel = self.card(self.main, self._c("surface"), 25); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        self.chat_box = ctk.CTkTextbox(panel, fg_color="transparent", text_color=self._c("text"), font=self._font(11), wrap="word"); self.chat_box.pack(fill="both", expand=True, padx=20, pady=20); self.chat_box.configure(state="disabled")
        if not self.chat_messages: self._chat_add("ATLAS", "Hey. What do you want to learn today?")
        else:
            for who, msg in self.chat_messages: self._chat_add(who, msg, False)
        bottom = ctk.CTkFrame(panel, fg_color=self._c("surface_2"), corner_radius=17); bottom.pack(fill="x", padx=15, pady=(0, 15))
        self.chat_input = ctk.CTkEntry(bottom, placeholder_text="Ask Atlas anything…", height=48, fg_color="transparent", border_width=0, text_color=self._c("text"), font=self._font(10)); self.chat_input.pack(side="left", fill="x", expand=True, padx=14); self.chat_input.bind("<Return>", lambda _e: self.send_chat())
        self.button(bottom, "🎙", self.show_voice, 48).pack(side="left", padx=4, pady=5); self.button(bottom, "Send  →", self.send_chat, 100, True).pack(side="right", padx=6, pady=5)

    def _chat_add(self, who, msg, store=True):
        if store: self.chat_messages.append((who, msg))
        if not hasattr(self, "chat_box"): return
        self.chat_box.configure(state="normal"); self.chat_box.insert("end", f"\n{who}\n{msg}\n"); self.chat_box.configure(state="disabled"); self.chat_box.see("end")

    def send_chat(self):
        if self.chat_busy or not hasattr(self, "chat_input"): return
        text = self.chat_input.get().strip()
        if not text: return
        self.chat_input.delete(0, "end"); self._chat_add("YOU", text); self.chat_busy = True; self._chat_add("ATLAS", "Thinking…")
        threading.Thread(target=self._chat_worker, args=(text,), daemon=True).start()

    def _chat_worker(self, text):
        try: answer = process(text)
        except Exception as exc: answer = f"I hit an error while processing that: {exc}"
        self.after(0, lambda a=answer: self._finish_chat(a))

    def _finish_chat(self, answer):
        self.chat_busy = False
        if self.chat_messages and self.chat_messages[-1][1] == "Thinking…": self.chat_messages.pop()
        self._chat_add("ATLAS", answer)

    def show_voice(self):
        self.set_active("Voice"); self.clear(); self.header("Voice Core", "Talk, don't type.", "Atlas can listen, reason and respond through the same brain.")
        panel = self.card(self.main, self._c("surface"), 28); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        ctk.CTkLabel(panel, text="✦", text_color=self._c("accent"), font=("Segoe UI Symbol", 110, "bold")).pack(pady=(80, 5))
        ctk.CTkLabel(panel, text="ATLAS IS LISTENING FOR YOU", text_color=self._c("text"), font=self._font(18, "bold")).pack()
        self.voice_status = ctk.CTkLabel(panel, text="READY · LOCAL VOICE" if VOICE_AVAILABLE else "VOICE ENGINE UNAVAILABLE", text_color=self._c("success") if VOICE_AVAILABLE else self._c("danger"), font=self._font(9, "bold")); self.voice_status.pack(pady=8)
        self.voice_hint = ctk.CTkLabel(panel, text="Press once, speak normally, and Atlas will answer.", text_color=self._c("muted"), font=self._font(10)); self.voice_hint.pack()
        controls = ctk.CTkFrame(panel, fg_color="transparent"); controls.pack(pady=25)
        self.listen_btn = self.button(controls, "◉  START LISTENING", self.start_voice, 230, True, 48); self.listen_btn.pack(side="left", padx=6)
        self.stop_voice_btn = self.button(controls, "■  STOP SPEAKING", self.stop_voice, 170, False, 48); self.stop_voice_btn.pack(side="left", padx=6)

    def start_voice(self):
        if self.voice_busy: return
        if not VOICE_AVAILABLE: self.voice_status.configure(text="VOICE ENGINE UNAVAILABLE", text_color=self._c("danger")); return
        self.voice_busy = True; self.listen_btn.configure(state="disabled", text="◉  LISTENING…"); self.voice_status.configure(text="LISTENING", text_color=self._c("accent")); threading.Thread(target=self._voice_worker, daemon=True).start()

    def stop_voice(self):
        if stop_speaking:
            try:
                stop_speaking()
            except Exception:
                pass
        self.voice_busy = False
        if hasattr(self, "voice_status"):
            self.voice_status.configure(text="READY · LOCAL VOICE", text_color=self._c("success"))
        if hasattr(self, "voice_hint"):
            self.voice_hint.configure(text="Speech stopped. Ready for your next question.")
        if hasattr(self, "listen_btn"):
            self.listen_btn.configure(state="normal", text="◉  START LISTENING")
    def _voice_worker(self):
        try:
            text = listen()
            if not text: raise RuntimeError("I didn't hear anything.")
            self.after(0, lambda: self.voice_status.configure(text="THINKING…")); answer = process(text); self.after(0, lambda: self.voice_status.configure(text="SPEAKING…", text_color=self._c("success"))); speak(answer); self.after(0, lambda: self._voice_done("READY · LOCAL VOICE", "Ready for your next question."))
        except Exception as exc: self.after(0, lambda e=str(exc): self._voice_done("VOICE ERROR", e))

    def _voice_done(self, status, hint):
        self.voice_busy = False; self.voice_status.configure(text=status, text_color=self._c("success") if "READY" in status else self._c("danger")); self.voice_hint.configure(text=hint); self.listen_btn.configure(state="normal", text="◉  START LISTENING")

    def show_subject(self, subject):
        self.set_active("Maths" if subject == "Mathematics" else subject); self.clear(); self.header(subject, f"Your {subject} space", "A focused place to understand, practice and improve.")
        grid = ctk.CTkFrame(self.main, fg_color="transparent"); grid.pack(fill="both", expand=True, padx=45, pady=(0, 28)); grid.grid_columnconfigure((0,1), weight=1); grid.grid_rowconfigure((0,1), weight=1)
        cards = [("01", "UNDERSTAND", "Learn the idea from first principles.", lambda: self.open_subject_chat(subject, "Teach me the key concepts")), ("02", "RECALL", "Build a compact formula and concept sheet.", lambda: self.open_subject_chat(subject, "Give me the important formulas and explain them")), ("03", "PRACTICE", "Use questions to turn knowledge into skill.", self.show_practice), ("04", "FIX WEAK SPOTS", "Ask Atlas what needs attention next.", lambda: self.open_subject_chat(subject, "What should I revise and practice next?"))]
        for i, (num, title, desc, cmd) in enumerate(cards):
            c = self.card(grid); c.grid(row=i//2, column=i%2, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(c, text=num, text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=25, pady=(25, 8)); ctk.CTkLabel(c, text=title, text_color=self._c("text"), font=self._font(20, "bold")).pack(anchor="w", padx=25); ctk.CTkLabel(c, text=desc, text_color=self._c("muted"), font=self._font(10), wraplength=450, justify="left").pack(anchor="w", padx=25, pady=(7, 20)); self.button(c, "Open  →", cmd, 115, True).pack(anchor="w", padx=25, pady=(0, 25))

    def open_subject_chat(self, subject, prompt):
        self.show_chat(); self.chat_input.insert(0, f"{subject}: {prompt}"); self.chat_input.focus()

    def show_notes(self):
        self.set_active("Notes"); self.clear(); self.header("Knowledge", "Your study shelf", "Capture explanations, summaries and useful discoveries.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28)); toolbar = ctk.CTkFrame(panel, fg_color="transparent"); toolbar.pack(fill="x", padx=20, pady=18); self.button(toolbar, "＋  New note", self.new_note, 125, True).pack(side="left"); self.button(toolbar, "Open PDF", self.import_pdf, 110).pack(side="left", padx=8); self.notes_box = ctk.CTkTextbox(panel, fg_color=self._c("surface_2"), text_color=self._c("text"), font=self._font(11), wrap="word"); self.notes_box.pack(fill="both", expand=True, padx=20, pady=(0,20)); self.notes_box.insert("1.0", "Your notes live here.\n\nUse Chat to understand a concept, then save the useful part here.")

    def new_note(self): self.notes_box.delete("1.0", "end"); self.notes_box.insert("1.0", f"# Study Note — {datetime.now():%d %b %Y}\n\n")

    def import_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        if not ingest_pdf:
            messagebox.showerror("Atlas Library", "PDF ingestion is unavailable.", parent=self)
            return
        class_level = simpledialog.askinteger("Atlas Library", "Class (9-12):", minvalue=9, maxvalue=12, parent=self)
        if class_level is None:
            return
        subject = simpledialog.askstring("Atlas Library", "Subject:", initialvalue="Physics", parent=self)
        if not subject or not subject.strip():
            return
        try:
            result = ingest_pdf(path, class_level, subject.strip())
            if result.get("status") == "skipped":
                messagebox.showinfo("Atlas Library", f"Already indexed — no re-index needed.\n\n{result.get('title', Path(path).stem)}", parent=self)
            else:
                extra = f"\nScanned pages needing OCR: {len(result.get('scanned_pages', []))}" if result.get("ocr_required") else ""
                messagebox.showinfo("Atlas Library", f"Indexed {result.get('title', Path(path).stem)}\nPages indexed: {result.get('pages_indexed', 0)}{extra}", parent=self)
        except Exception as exc:
            messagebox.showerror("Atlas Library", f"Import failed:\n{exc}", parent=self)

    def show_practice(self):
        self.set_active("Practice")
        self.clear()
        self.header("Practice Lab", "Turn knowledge into skill", "Atlas adapts difficulty from your actual attempts.")
        panel = self.card(self.main)
        panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        ctk.CTkLabel(panel, text="PRACTICE BUILDER", text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=28, pady=(28, 7))
        row = ctk.CTkFrame(panel, fg_color="transparent"); row.pack(fill="x", padx=24, pady=14)
        subject = ctk.CTkOptionMenu(row, values=["Physics", "Mathematics", "Chemistry"], width=170); subject.pack(side="left")
        topic = ctk.CTkEntry(row, placeholder_text="Topic / chapter", height=42); topic.pack(side="left", fill="x", expand=True, padx=10)
        count = ctk.CTkOptionMenu(row, values=["5", "10", "15"], width=80); count.set("5"); count.pack(side="left")
        output = ctk.CTkTextbox(panel, fg_color=self._c("surface_2"), text_color=self._c("text"), font=self._font(10), wrap="word")
        output.pack(fill="both", expand=True, padx=24, pady=(4, 18))
        def build():
            topic_name = topic.get().strip()
            if not topic_name:
                output.delete("1.0", "end"); output.insert("1.0", "Enter a topic first."); return
            subject_name = subject.get()
            state = self.learning.topic(subject_name, topic_name)
            items = self.learning.practice_plan(subject_name, topic_name, int(count.get()))
            output.delete("1.0", "end")
            output.insert("1.0", f"{subject_name} · {topic_name}\nCurrent mastery: {state.get('mastery', 0)}%\nNext difficulty: {self.learning.next_difficulty(subject_name, topic_name)}\n\n")
            for item in items:
                output.insert("end", f"{item['index']}. Difficulty {item['difficulty']} · Practice question\n")
            output.insert("end", "\nUse Chat to generate the actual questions; after each answer, record the result so Atlas can adapt.")
        self.button(row, "Build plan", build, 115, True).pack(side="left", padx=(10, 0))

    def show_planner(self):
        self.set_active("Planner"); self.clear(); self.header("Planning", "Your study rhythm", "A simple plan that keeps the important things moving.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=45,pady=(0,28));
        for time_,task in [("16:00","Tuition"),("20:00","Physics · focused study"),("20:45","Mathematics · practice"),("21:30","Chemistry · review")]:
            row=ctk.CTkFrame(panel,fg_color=self._c("surface_2"),corner_radius=14); row.pack(fill="x",padx=25,pady=6); ctk.CTkLabel(row,text=time_,text_color=self._c("accent"),font=self._font(10,"bold"),width=75).pack(side="left",padx=14,pady=14); ctk.CTkLabel(row,text=task,text_color=self._c("text"),font=self._font(10,"bold")).pack(side="left")
        self.button(panel,"Ask Atlas to build a plan",lambda:self.open_subject_chat("Study","Build me a focused study plan."),220,True).pack(anchor="w",padx=25,pady=22)

    def show_settings(self):
        self.set_active("Settings")
        self.clear()
        self.header("Settings", "Control your Atlas", "Profile, privacy, theme and local backups live here.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        profile = self.education_profile.data()
        ctk.CTkLabel(panel, text="STUDENT PROFILE", text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=25, pady=(24, 8))
        form = ctk.CTkFrame(panel, fg_color="transparent"); form.pack(fill="x", padx=20)
        name_entry = ctk.CTkEntry(form, placeholder_text="Your name", height=40)
        try:
            current_name = self.memory.recall("name") if self.memory else ""
        except Exception:
            current_name = ""
        if current_name:
            name_entry.insert(0, str(current_name))
        name_entry.pack(side="left", fill="x", expand=True, padx=5)
        class_entry = ctk.CTkEntry(form, placeholder_text="Class (1-12)", height=40); class_entry.insert(0, str(profile.get("primary_class") or "")); class_entry.pack(side="left", fill="x", expand=True, padx=5)
        subject_entry = ctk.CTkEntry(form, placeholder_text="Primary subject", height=40); subject_entry.insert(0, str(profile.get("primary_subject") or "")); subject_entry.pack(side="left", fill="x", expand=True, padx=5)
        prefs = profile.get("learning_preferences", {})
        style_entry = ctk.CTkEntry(form, placeholder_text="Teaching style", height=40); style_entry.insert(0, str(prefs.get("teaching_style", "step_by_step"))); style_entry.pack(side="left", fill="x", expand=True, padx=5)
        def save_profile():
            try:
                name = name_entry.get().strip()
                if name and self.memory:
                    self.memory.remember("name", name, source="user_settings", importance=0.95)
                if class_entry.get().strip():
                    self.education_profile.set_class(int(class_entry.get().strip()))
                self.education_profile.set_subject(subject_entry.get().strip())
                self.education_profile.set_preferences(teaching_style=style_entry.get().strip() or "step_by_step")
                messagebox.showinfo("Atlas", "Student profile saved locally.", parent=self)
            except Exception as exc:
                messagebox.showerror("Atlas", f"Could not save profile:\n{exc}", parent=self)
        self.button(panel, "Save profile", save_profile, 140, True).pack(anchor="w", padx=25, pady=14)
        ctk.CTkLabel(panel, text="LOCAL DATA", text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=25, pady=(10, 8))
        data_row = ctk.CTkFrame(panel, fg_color="transparent"); data_row.pack(fill="x", padx=20)
        def do_export():
            path=filedialog.asksaveasfilename(defaultextension=".atlas-backup.json", filetypes=[("Atlas backup","*.atlas-backup.json"),("JSON","*.json")], parent=self)
            if path:
                try:
                    export_backup(path); messagebox.showinfo("Atlas", "Backup exported.", parent=self)
                except Exception as exc: messagebox.showerror("Atlas", f"Backup failed:\n{exc}", parent=self)
        def do_restore():
            path=filedialog.askopenfilename(filetypes=[("Atlas backup","*.atlas-backup.json *.json"),("JSON","*.json")], parent=self)
            if path and messagebox.askyesno("Restore Atlas", "Restore local Atlas data from this backup?", parent=self):
                try:
                    restored=restore_bundle(path)
                    messagebox.showinfo("Atlas", f"Restored {len(restored)} JSON files. Restart Atlas to reload all services.", parent=self)
                except Exception as exc: messagebox.showerror("Atlas", f"Restore failed:\n{exc}", parent=self)
        self.button(data_row, "Export backup", do_export, 140).pack(side="left", padx=5)
        self.button(data_row, "Restore backup", do_restore, 140).pack(side="left", padx=5)
        ctk.CTkLabel(panel, text="THEME", text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=25, pady=(22, 8))
        self.button(panel, "Open Atlas Studio", self.show_studio, 170, True).pack(anchor="w", padx=25)
        ctk.CTkLabel(panel, text="Theme changes in Studio are live and saved locally; no restart is needed for the open window.", text_color=self._c("muted"), font=self._font(9), wraplength=650, justify="left").pack(anchor="w", padx=25, pady=10)

    def show_memory(self):
        self.set_active("Memory")
        self.clear()
        self.header("Long-term memory", "What Atlas remembers", "Search, inspect, and forget durable memories with explicit user control.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        toolbar = ctk.CTkFrame(panel, fg_color="transparent"); toolbar.pack(fill="x", padx=20, pady=15)
        query = ctk.CTkEntry(toolbar, placeholder_text="Search memory…", height=40); query.pack(side="left", fill="x", expand=True)
        box = ctk.CTkTextbox(panel, fg_color=self._c("surface_2"), text_color=self._c("text"), font=self._font(10)); box.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        def render(items=None):
            try:
                records = items if items is not None else self.memory.get_all_records(include_archived=False)
                box.configure(state="normal"); box.delete("1.0", "end")
                if not records:
                    box.insert("1.0", "No active durable memories.")
                else:
                    for item in records:
                        label = item.get("key") or item.get("type", "memory")
                        box.insert("end", f"[{label}]\n{item.get('content', item.get('value', ''))}\nID: {item.get('id', '')}\n\n")
                box.configure(state="disabled")
            except Exception as exc:
                box.configure(state="normal"); box.delete("1.0", "end"); box.insert("end", f"Memory interface unavailable: {exc}"); box.configure(state="disabled")
        def search():
            text = query.get().strip()
            render(self.memory.search(text, limit=20) if text and self.memory else [])
        def forget():
            text = query.get().strip()
            if not text or not self.memory:
                return
            if not messagebox.askyesno("Forget memory", f"Forget memories matching:\n\n{text}", parent=self):
                return
            self.memory.archive_matching(text)
            render()
        self.button(toolbar, "Search", search, 100, True).pack(side="left", padx=7)
        self.button(toolbar, "Forget match", forget, 120).pack(side="left")
        render()

    def show_progress(self):
        self.set_active("Progress")
        self.clear()
        self.header("Learning analytics", "See your momentum", "Numbers are derived from actual sessions, attempts, revisions and goals.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        data = self.learning.data()
        attempts = data.get("attempts", [])
        revisions = data.get("revisions", [])
        ctk.CTkLabel(panel, text=f"{len(attempts)} practice attempts · {len(revisions)} revision events", text_color=self._c("muted"), font=self._font(10)).pack(anchor="w", padx=26, pady=(22, 14))
        topics = list(data.get("topics", {}).values())
        if not topics:
            ctk.CTkLabel(panel, text="No topic attempts recorded yet. Start with Practice.", text_color=self._c("muted"), font=self._font(10)).pack(anchor="w", padx=26, pady=18)
        for item in sorted(topics, key=lambda x: x.get("mastery", 0))[:10]:
            self._progress_row(panel, f"{item.get('subject')} · {item.get('topic')}", float(item.get("mastery", 0)) / 100)
        insights = self.growth.insights()
        ctk.CTkLabel(panel, text=f"Growth: {insights.get('active_goals', 0)} active goals · {insights.get('history_events', 0)} history events", text_color=self._c("muted"), font=self._font(9)).pack(anchor="w", padx=26, pady=12)

    def _progress_row(self,parent,subject,value):
        row=ctk.CTkFrame(parent,fg_color="transparent"); row.pack(fill="x",padx=26,pady=8)
        ctk.CTkLabel(row,text=subject,text_color=self._c("text"),font=self._font(10,"bold")).pack(side="left")
        ctk.CTkLabel(row,text=f"{int(value*100)}%",text_color=self._c("muted"),font=self._font(9)).pack(side="right")
        b=ctk.CTkProgressBar(parent,height=7,progress_color=self._c("accent"),fg_color=self._c("border")); b.pack(fill="x",padx=26); b.set(max(0,min(1,value)))

    # ---------------- Studio: unlocked after seven days ----------------
    def show_studio(self):
        if self.days_used < 7:
            self._studio_locked(); return
        self.set_active("Studio"); self.clear(); self.header("Atlas Studio", "Make Atlas yours", "Change the visual language, spacing, colors, background and feel.")
        shell=ctk.CTkFrame(self.main,fg_color="transparent"); shell.pack(fill="both",expand=True,padx=38,pady=(0,25)); shell.grid_columnconfigure(0,weight=1); shell.grid_columnconfigure(1,weight=1); shell.grid_rowconfigure(1,weight=1)
        tabs=ctk.CTkTabview(shell,fg_color=self._c("surface"),segmented_button_fg_color=self._c("surface_2"),segmented_button_selected_color=self._c("accent"),segmented_button_selected_hover_color=self._c("accent_2"),corner_radius=20); tabs.grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,10))
        for name in ["Theme","Layout","Behavior","Advanced"]: tabs.add(name)
        self._studio_theme(tabs.tab("Theme")); self._studio_layout(tabs.tab("Layout")); self._studio_behavior(tabs.tab("Behavior")); self._studio_advanced(tabs.tab("Advanced"))
        controls=self.card(shell); controls.grid(row=1,column=0,sticky="nsew",padx=(0,7)); preview=self.card(shell); preview.grid(row=1,column=1,sticky="nsew",padx=(7,0)); self._studio_preview(preview)
        self.button(controls,"Apply & Save",self._studio_save,170,True).pack(anchor="w",padx=22,pady=(22,7)); self.button(controls,"Reset Atlas",self._studio_reset,170).pack(anchor="w",padx=22,pady=7); self.button(controls,"Export Theme",self._studio_export,170).pack(anchor="w",padx=22,pady=7); self.button(controls,"Import Theme",self._studio_import,170).pack(anchor="w",padx=22,pady=7)

    def _studio_locked(self):
        self.set_active("Studio"); self.clear(); self.header("Atlas Studio", "A little later.", "Atlas wants to learn how you use it before asking you to redesign it.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=45,pady=(0,28)); ctk.CTkLabel(panel,text="✦",text_color=self._c("accent"),font=("Segoe UI Symbol",90,"bold")).pack(pady=(100,10)); ctk.CTkLabel(panel,text=f"Studio unlocks after 7 days · Day {self.days_used}/7",text_color=self._c("text"),font=self._font(20,"bold")).pack(); ctk.CTkLabel(panel,text="Use Atlas normally first. Once it understands your rhythm,\nyou'll get full control over the look and feel.",text_color=self._c("muted"),font=self._font(10),justify="center").pack(pady=12)

    def _studio_theme(self,p):
        ctk.CTkLabel(p,text="LIVE COLORS",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",padx=18,pady=(14,6))
        for label,key in [("Background","background"),("Background glow","background_2"),("Surface","surface"),("Surface raised","surface_2"),("Text","text"),("Muted","muted"),("Accent","accent"),("Accent secondary","accent_2"),("Border","border")]: self._color_control(p,label,key)
        self._choice(p,"Background style","background_style",["Aurora","Midnight"])

    def _color_control(self,parent,label,key):
        row=ctk.CTkFrame(parent,fg_color="transparent"); row.pack(fill="x",padx=15,pady=3); ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=150,anchor="w").pack(side="left"); sw=ctk.CTkButton(row,text=self.ui[key],width=105,height=30,fg_color=self.ui[key],hover_color=self.ui[key],text_color=self._c("text"),command=lambda k=key:self._pick_color(k)); sw.pack(side="left"); setattr(self,f"sw_{key}",sw)

    def _pick_color(self,key):
        picked=colorchooser.askcolor(color=self.ui[key],title=f"Atlas Studio · {key}")[1]
        if picked:
            self.ui[key]=picked; getattr(self,f"sw_{key}").configure(text=picked,fg_color=picked,hover_color=picked); self._live_studio_refresh()

    def _studio_layout(self,p):
        self._slider(p,"Sidebar width","sidebar_width",190,330,1); self._slider(p,"Corner radius","radius",10,32,1); self._slider(p,"UI scale","ui_scale",.85,1.25,.01); self._slider(p,"Window opacity","opacity",.8,1,.01); self._slider(p,"Base font size","font_size",9,15,1); self._slider(p,"Title size","title_size",24,42,1); self._choice(p,"Font","font",["Segoe UI","Arial","Calibri","Tahoma","Consolas"])

    def _studio_behavior(self,p):
        self._slider(p,"Animation speed (ms)","animation_ms",70,500,10); self._switch(p,"Show sidebar","show_sidebar"); self._switch(p,"Show core status","show_status"); self._switch(p,"Show date","show_date")

    def _studio_advanced(self,p):
        self.raw_box=ctk.CTkTextbox(p,fg_color=self._c("surface_2"),text_color=self._c("text"),font=("Consolas",10)); self.raw_box.pack(fill="both",expand=True,padx=14,pady=14); self.raw_box.insert("1.0",json.dumps(self.ui,indent=2)); self.button(p,"Apply JSON",self._apply_raw,120,True).pack(anchor="e",padx=14,pady=(0,14))

    def _slider(self,p,label,key,a,b,step):
        row=ctk.CTkFrame(p,fg_color="transparent"); row.pack(fill="x",padx=15,pady=6); lbl=ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=165,anchor="w"); lbl.pack(side="left"); value=ctk.CTkLabel(row,text=str(self.ui[key]),text_color=self._c("muted"),width=55); value.pack(side="right"); scale=ctk.CTkSlider(row,from_=a,to=b,number_of_steps=max(1,int((b-a)/step)),command=lambda v,k=key,l=value,s=step:self._set_slider(k,v,l,s),progress_color=self._c("accent")); scale.set(self.ui[key]); scale.pack(side="left",fill="x",expand=True,padx=7)

    def _set_slider(self,key,v,label,step):
        self.ui[key]=round(float(v),2) if step < 1 else int(round(float(v))); label.configure(text=str(self.ui[key])); self._live_studio_refresh()

    def _switch(self,p,label,key):
        sw=ctk.CTkSwitch(p,text=label,text_color=self._c("text"),progress_color=self._c("accent"),button_color=self._c("text")); sw.pack(anchor="w",padx=18,pady=7); sw.select() if self.ui[key] else sw.deselect(); sw.configure(command=lambda k=key,s=sw:self._set_switch(k,s))

    def _set_switch(self,key,sw): self.ui[key]=bool(sw.get()); self._live_studio_refresh()

    def _choice(self,p,label,key,values):
        row=ctk.CTkFrame(p,fg_color="transparent"); row.pack(fill="x",padx=15,pady=6); ctk.CTkLabel(row,text=label,text_color=self._c("text"),font=self._font(9),width=165,anchor="w").pack(side="left"); menu=ctk.CTkOptionMenu(row,values=values,fg_color=self._c("surface_2"),button_color=self._c("accent"),text_color=self._c("text"),command=lambda v,k=key:self._set_choice(k,v)); menu.set(self.ui[key]); menu.pack(side="left",fill="x",expand=True)

    def _set_choice(self,key,v): self.ui[key]=v; self._live_studio_refresh()

    def _studio_preview(self,parent):
        ctk.CTkLabel(parent,text="LIVE CANVAS",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",padx=20,pady=(20,8)); self.preview=ctk.CTkFrame(parent,fg_color=self._c("background"),corner_radius=self.ui["radius"]); self.preview.pack(fill="both",expand=True,padx=18,pady=(0,18)); self.preview_orb=ctk.CTkLabel(self.preview,text="✦",text_color=self._c("accent"),font=("Segoe UI Symbol",62,"bold")); self.preview_orb.pack(pady=(40,3)); ctk.CTkLabel(self.preview,text="ATLAS",text_color=self._c("text"),font=self._font(22,"bold")).pack(); ctk.CTkLabel(self.preview,text="A calm space for deep learning",text_color=self._c("muted"),font=self._font(9)).pack(pady=4); row=ctk.CTkFrame(self.preview,fg_color="transparent"); row.pack(fill="x",padx=22,pady=20)
        for title,cmd in [("CHAT",self.show_chat),("VOICE",self.show_voice),("PRACTICE",self.show_practice)]: self._preview_tile(row,title,cmd)

    def _preview_tile(self,parent,title,cmd):
        tile=ctk.CTkFrame(parent,fg_color=self._c("surface"),corner_radius=16,border_width=1,border_color=self._c("border")); tile.pack(side="left",fill="x",expand=True,padx=4); ctk.CTkLabel(tile,text=title,text_color=self._c("text"),font=self._font(9,"bold")).pack(pady=(15,3)); ctk.CTkLabel(tile,text="Open →",text_color=self._c("accent"),font=self._font(8)).pack(pady=(0,15)); tile.bind("<Button-1>",lambda _e,c=cmd:c())

    def _live_studio_refresh(self):
        save_ui(self.ui); self._apply_window(); self._build_shell(); self.show_studio();

    def _studio_save(self): save_ui(self.ui); self._apply_window(); self._build_shell(); self.show_studio()
    def _studio_reset(self): self.ui=deepcopy(DEFAULT_UI); save_ui(self.ui); self._apply_window(); self._build_shell(); self.show_studio()

    def _apply_raw(self):
        try:
            data=json.loads(self.raw_box.get("1.0","end")); merged=deepcopy(DEFAULT_UI); merged.update(data); self.ui=merged; save_ui(self.ui); self._apply_window(); self._build_shell(); self.show_studio()
        except Exception as exc: messagebox.showerror("Atlas Studio","Invalid UI JSON: "+str(exc))

    def _studio_export(self):
        path=filedialog.asksaveasfilename(defaultextension=".atlas-theme",filetypes=[("Atlas Theme","*.atlas-theme"),("JSON","*.json")],initialfile="my-atlas-theme.atlas-theme")
        if path: Path(path).write_text(json.dumps(self.ui,indent=2,ensure_ascii=False),encoding="utf-8")

    def _studio_import(self):
        path=filedialog.askopenfilename(filetypes=[("Atlas Theme","*.atlas-theme *.json"),("All files","*.*")])
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8")); merged=deepcopy(DEFAULT_UI); merged.update(data); self.ui=merged; save_ui(self.ui); self._apply_window(); self._build_shell(); self.show_studio()
        except Exception as exc: messagebox.showerror("Atlas Studio","Could not import theme: "+str(exc))

    def toggle_command_center(self):
        if self.command_overlay: self.close_command_center(); return
        self.command_overlay=ctk.CTkFrame(self.stage,fg_color=self._c("surface"),corner_radius=25,border_width=1,border_color=self._c("border"),width=600,height=360); self.command_overlay.place(relx=.52,rely=.14,anchor="n"); ctk.CTkLabel(self.command_overlay,text="ATLAS COMMAND CENTER",text_color=self._c("accent"),font=self._font(8,"bold")).pack(anchor="w",padx=25,pady=(23,5)); ctk.CTkLabel(self.command_overlay,text="Where should we go?",text_color=self._c("text"),font=self._font(23,"bold")).pack(anchor="w",padx=25,pady=(0,13)); entry=ctk.CTkEntry(self.command_overlay,placeholder_text="Try: physics, voice, studio, practice…",height=45,fg_color=self._c("surface_2"),border_width=0); entry.pack(fill="x",padx=20,pady=(0,13)); entry.focus(); actions=[("Chat",self.show_chat),("Voice",self.show_voice),("Practice",self.show_practice),("Progress",self.show_progress),("Notes",self.show_notes),("Planner",self.show_planner)]; grid=ctk.CTkFrame(self.command_overlay,fg_color="transparent"); grid.pack(fill="x",padx=18)
        for i,(label,cmd) in enumerate(actions): self.button(grid,label,lambda c=cmd:self._command_run(c),165).grid(row=i//2,column=i%2,padx=4,pady=4)
        entry.bind("<Return>",lambda _e:self._command_search(entry.get()))

    def _command_run(self,c): self.close_command_center(); c()
    def _command_search(self,text):
        t=text.lower(); mapping=[("studio",self.show_studio),("voice",self.show_voice),("chat",self.show_chat),("practice",self.show_practice),("progress",self.show_progress),("note",self.show_notes),("planner",self.show_planner),("memory",self.show_memory),("physics",lambda:self.show_subject("Physics")),("math",lambda:self.show_subject("Mathematics")),("chem",lambda:self.show_subject("Chemistry"))]
        for key,cmd in mapping:
            if key in t:return self._command_run(cmd)

    def close_command_center(self):
        if self.command_overlay: self.command_overlay.destroy(); self.command_overlay=None


def main():
    app=AtlasGUI(); app.mainloop()


if __name__ == "__main__":
    main()
