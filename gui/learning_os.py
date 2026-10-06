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
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk
import tkinter as tk

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.agent import process
try:
    from student.atlas_student import system as student_system
except Exception:
    student_system = None

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

DEFAULT_UI = {
    "background": "#070A12",
    "background_2": "#10152A",
    "sidebar": "#0A0D17",
    "surface": "#111625",
    "surface_2": "#171D2F",
    "surface_hover": "#202943",
    "text": "#F7F8FC",
    "muted": "#929AB0",
    "accent": "#8EA7FF",
    "accent_2": "#B58CFF",
    "success": "#72D7AD",
    "warning": "#F1C56D",
    "danger": "#EF8E9A",
    "border": "#293149",
    "font": "Segoe UI",
    "font_size": 11,
    "title_size": 32,
    "radius": 22,
    "sidebar_width": 250,
    "ui_scale": 1.0,
    "opacity": 1.0,
    "animation_ms": 180,
    "background_style": "Aurora",
    "show_sidebar": True,
    "show_status": True,
    "show_date": True,
    "theme": "dark",
    "ui_version": 2,
}

LIGHT_OVERRIDES = {
    "background": "#F4F7FF",
    "background_2": "#E6ECFF",
    "sidebar": "#F8FAFF",
    "surface": "#FFFFFF",
    "surface_2": "#EEF2FF",
    "surface_hover": "#E3E9FF",
    "text": "#18203A",
    "muted": "#68718A",
    "accent": "#5B63FF",
    "accent_2": "#8B5CF6",
    "border": "#D7DDF2",
}
APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
UI_FILE = APPDATA / "ui.json"
FIRST_USE_FILE = APPDATA / "first_use.json"


def load_ui():
    try:
        APPDATA.mkdir(parents=True, exist_ok=True)
        if UI_FILE.exists():
            data = json.loads(UI_FILE.read_text(encoding="utf-8"))
            out = deepcopy(DEFAULT_UI)
            out.update({k: v for k, v in data.items() if k in out})
            if int(data.get("ui_version", 0) or 0) < 2:
                out = deepcopy(DEFAULT_UI)
            out["ui_version"] = 2
            return out
    except Exception:
        pass
    return deepcopy(DEFAULT_UI)


def save_ui(data):
    APPDATA.mkdir(parents=True, exist_ok=True)
    UI_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


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
        self._particles = []
        self._apply_window()
        self._build_shell()
        self.bind("<Control-space>", lambda _e: self.toggle_command_center())
        self.bind("<Escape>", lambda _e: self.close_command_center())
        self.show_home()
        self.after(120, self._animate_background)

    def _apply_window(self):
        theme = self.ui.get("theme", "dark")
        ctk.set_appearance_mode("dark" if theme == "dark" else "light")
        self.configure(fg_color=self.ui["background"])
        try:
            self.attributes("-alpha", float(self.ui["opacity"]))
        except Exception:
            pass

    def _c(self, key):
        return self.ui[key]

    def _font(self, size=None, weight=None):
        """Return the configured UI font tuple used throughout the shell."""
        family = self.ui.get("font", "Segoe UI")
        base = float(self.ui.get("font_size", 11))
        actual = int(round(float(size if size is not None else base)))
        if self.ui.get("ui_scale", 1.0) != 1.0:
            actual = max(7, int(round(actual * float(self.ui.get("ui_scale", 1.0)))))
        return (family, actual, weight) if weight else (family, actual)

    def _profile(self):
        try:
            return student_system.intelligence.profile() if student_system else {}
        except Exception:
            return {}

    def _snapshot(self):
        try:
            return student_system.dashboard() if student_system else {}
        except Exception:
            return {}

    def _display_name(self):
        profile = self._profile()
        return str(profile.get("name") or profile.get("student_name") or "Student")

    def _display_class(self):
        profile = self._profile()
        value = profile.get("class") or profile.get("grade") or profile.get("standard")
        return str(value) if value else "Student profile"

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

        self.topbar = ctk.CTkFrame(
            self.stage, fg_color="transparent", corner_radius=0,
            border_width=0, height=62
        )
        self.topbar.pack(side="top", fill="x")
        self.topbar.pack_propagate(False)

        brand = ctk.CTkFrame(self.topbar, fg_color="transparent")
        brand.pack(side="left", padx=24)
        ctk.CTkLabel(brand, text="✦", text_color=self._c("accent"),
                     font=("Segoe UI Symbol", 25, "bold")).pack(side="left")
        ctk.CTkLabel(brand, text="ATLAS", text_color=self._c("text"),
                     font=self._font(16, "bold")).pack(side="left", padx=(10, 0))

        search = ctk.CTkEntry(
            self.topbar, placeholder_text="Search Atlas", width=280, height=38,
            corner_radius=19, fg_color=self._c("surface_2"), border_width=0,
            text_color=self._c("text"), placeholder_text_color=self._c("muted"),
            font=self._font(9)
        )
        search.pack(side="left", padx=24)

        profile = ctk.CTkFrame(self.topbar, fg_color="transparent")
        profile.pack(side="right", padx=18)
        ctk.CTkButton(
            profile, text="☼" if self.ui.get("theme") == "dark" else "☾",
            width=38, height=38, corner_radius=19,
            fg_color=self._c("surface_2"), hover_color=self._c("surface_hover"),
            text_color=self._c("text"), font=self._font(12, "bold"),
            command=self.toggle_theme
        ).pack(side="left", padx=5)
        avatar = ctk.CTkFrame(profile, width=38, height=38, fg_color=self._c("accent"), corner_radius=19)
        avatar.pack(side="left", padx=7)
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=self._display_name()[:1].upper(),
                     text_color="#FFFFFF", font=self._font(12, "bold")).place(relx=.5, rely=.5, anchor="center")
        info = ctk.CTkFrame(profile, fg_color="transparent")
        info.pack(side="left", padx=(3, 8))
        ctk.CTkLabel(info, text=self._display_name(), text_color=self._c("text"),
                     font=self._font(10, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=self._display_class(), text_color=self._c("muted"),
                     font=self._font(7)).pack(anchor="w")
        ctk.CTkButton(profile, text="⚙", width=34, height=34, corner_radius=17,
                      fg_color="transparent", hover_color=self._c("surface_hover"),
                      text_color=self._c("muted"), font=self._font(12),
                      command=self.show_studio).pack(side="left")

        body = ctk.CTkFrame(self.stage, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self.rail = ctk.CTkFrame(body, width=214, fg_color=self._c("sidebar"),
                                 corner_radius=0, border_width=0)
        if self.ui["show_sidebar"]:
            self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        nav_brand = ctk.CTkFrame(self.rail, fg_color="transparent")
        nav_brand.pack(fill="x", padx=18, pady=(22, 14))
        ctk.CTkLabel(nav_brand, text="ATLAS", text_color=self._c("text"),
                     font=self._font(18, "bold")).pack(anchor="w")
        ctk.CTkLabel(nav_brand, text="YOUR PERSONAL LEARNING SPACE",
                     text_color=self._c("muted"), font=self._font(7, "bold")).pack(anchor="w", pady=(2, 0))

        self.nav_buttons = {}
        nav = [
            ("◈", "Focus", self.show_home, "Your current sphere"),
            ("✧", "Learning", self.show_learning, "Build your tomorrow"),
            ("◌", "Memory", self.show_memory, "Nothing is ever lost"),
            ("◇", "Goals", self.show_goals, "Turn plans into reality"),
            ("▣", "Knowledge", self.show_notes, "Your personal library"),
            ("◉", "Self", self.show_self, "Understand yourself"),
        ]
        for icon, label, command, subtitle in nav:
            self._nav_button(icon, label, command, subtitle=subtitle)

        status = ctk.CTkFrame(self.rail, fg_color=self._c("surface"), corner_radius=16,
                              border_width=1, border_color=self._c("border"))
        status.pack(side="bottom", fill="x", padx=12, pady=14)
        ctk.CTkLabel(status, text="●", text_color=self._c("success"),
                     font=self._font(9)).pack(side="left", padx=(11, 6), pady=10)
        ctk.CTkLabel(status, text="Atlas is with you", text_color=self._c("text"),
                     font=self._font(8, "bold")).pack(anchor="w", pady=10)
        ctk.CTkLabel(status, text="Always. Always learning.", text_color=self._c("muted"),
                     font=self._font(6)).pack(anchor="w", padx=(27, 8), pady=(0, 10))

        self.main = ctk.CTkFrame(body, fg_color="transparent", corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def _draw_background(self):
        self.bg_canvas.delete("all")
        self._particles = []
        w = max(self.winfo_width(), 1280)
        h = max(self.winfo_height(), 760)
        self.bg_canvas.create_rectangle(0, 0, w, h, fill="#030611", outline="")
        self.bg_canvas.create_oval(w*.18, -h*.40, w*.86, h*.90, fill="#07112A", outline="")
        self.bg_canvas.create_oval(w*.40, -h*.28, w*1.10, h*.76, fill="#0B1230", outline="")
        self.bg_canvas.create_oval(-w*.22, h*.46, w*.58, h*1.28, fill="#090A25", outline="")
        self.bg_canvas.create_oval(w*.32, h*.15, w*.84, h*.86, fill="#10134A", outline="")
        self.bg_canvas.create_oval(w*.47, h*.20, w*.73, h*.72, fill="#17105A", outline="")
        cx, cy = w*.53, h*.48
        for i, color in enumerate(("#0D1740", "#101A4C", "#17185A", "#1D1769")):
            r = min(w, h) * (.30 - i*.045)
            self.bg_canvas.create_oval(cx-r, cy-r*.72, cx+r, cy+r*.72, fill=color, outline="")
        for i in range(70):
            x = (i * 173 + 97) % w
            y = (i * 97 + 31) % h
            r = 1 if i % 4 else 2
            fill = "#5D7DFF" if i % 7 == 0 else "#263A78"
            self._particles.append(self.bg_canvas.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline=""))

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

    def _nav_button(self, icon, label, command, subtitle="", bottom=False):
        holder = ctk.CTkFrame(self.rail, fg_color="transparent", corner_radius=14)
        holder.pack(side="bottom" if bottom else "top", fill="x", padx=10, pady=3)
        b = ctk.CTkButton(
            holder, text=f"{icon}   {label}", command=command, anchor="w",
            height=38, fg_color="transparent", hover_color=self._c("surface_hover"),
            text_color=self._c("muted"), corner_radius=13, font=self._font(10, "bold")
        )
        b.pack(fill="x")
        if subtitle:
            ctk.CTkLabel(holder, text=subtitle, text_color=self._c("muted"),
                         font=self._font(6)).pack(anchor="w", padx=38, pady=(0, 3))
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
        self.current_page = "home"
        self.set_active("Focus")
        self.clear()
        snap = self._snapshot()
        intel = snap.get("intelligence", {}) if isinstance(snap, dict) else {}
        adaptive = snap.get("adaptive_path", []) if isinstance(snap, dict) else []
        progress = snap.get("progress", {}) if isinstance(snap, dict) else {}
        profile = self._profile()
        name = profile.get("name") or self._display_name()
        weak = adaptive[0] if adaptive else {}
        focus_text = f"{weak.get('subject', 'Physics')} · {weak.get('topic', 'Your next review')}" if isinstance(weak, dict) else "Your next review"
        sessions = progress.get("sessions", []) if isinstance(progress, dict) else []
        recent = sessions[-1] if sessions else {}
        recent_text = f"{recent.get('subject', 'Study')} · {recent.get('topic') or 'Just now'}" if isinstance(recent, dict) else "No recent session"
        memory_count = int(snap.get("memory_items", 0) or 0) if isinstance(snap, dict) else 0
        goals = intel.get("goals", []) if isinstance(intel, dict) else []
        active_goals = len([g for g in goals if isinstance(g, dict) and not g.get("done")])
        knowledge_text = f"{len(snap.get('phases', []))} learning phases" if isinstance(snap, dict) and snap.get("phases") else "Your personal library"
        conversation_text = f"{snap.get('recent_messages', 0)} recent messages" if snap else "Ready when you are"

        visual = ctk.CTkFrame(self.main, fg_color="transparent")
        visual.pack(fill="both", expand=True, padx=(18, 10), pady=(8, 18))
        canvas = tk.Canvas(visual, highlightthickness=0, bd=0, bg="#030611", relief="flat")
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.core_canvas = canvas

        actions = ctk.CTkFrame(visual, fg_color="#080D20", corner_radius=24, border_width=1, border_color="#27366E", width=238)
        actions.place(relx=.985, rely=.055, relwidth=.205, relheight=.79, anchor="ne")
        ctk.CTkLabel(actions, text="Quick Actions", text_color="#F5F7FF", font=self._font(14, "bold")).pack(anchor="w", padx=18, pady=(18, 14))
        for icon, title, caption, cmd in [
            ("⌕", "Ask a Question", "Get instant help", self.show_chat),
            ("◈", "Start Study Session", "Focus mode", self.show_learning),
            ("▣", "Open Library", "Resources & notes", self.show_notes),
            ("↗", "Check Progress", "View your growth", self.show_progress),
            ("⚙", "Customize Atlas", "Make it yours", self.show_studio),
        ]:
            self._quick_action(actions, icon, title, caption, cmd)
        quote = ctk.CTkFrame(actions, fg_color="#0E1430", corner_radius=18, border_width=1, border_color="#252D5C")
        quote.pack(fill="x", padx=12, pady=(12, 12), side="bottom")
        ctk.CTkLabel(quote, text="“", text_color="#A78BFA", font=self._font(22, "bold")).pack(anchor="w", padx=12, pady=(6, 0))
        ctk.CTkLabel(quote, text="Small steps, consistent effort,\\ncreate extraordinary results.", text_color="#DDE4FF", font=self._font(8), justify="left").pack(anchor="w", padx=13)
        ctk.CTkLabel(quote, text="— Atlas", text_color="#7884AD", font=self._font(7)).pack(anchor="w", padx=13, pady=(2, 9))

        cards = [
            ("◈", "TODAY'S FOCUS", focus_text, "Physics · Electromagnetism", .08, .045),
            ("✧", "RECENT LEARNING", recent_text, "Just now", .69, .075),
            ("▣", "RECENT MEMORY", f"{memory_count} approved memories", "Long-term learning", .06, .34),
            ("▤", "KNOWLEDGE", knowledge_text, "Resources & notes", .73, .39),
            ("◆", "ACTIVE GOALS", f"{active_goals} active goals", "Turn plans into reality", .17, .63),
            ("◌", "CONVERSATION", conversation_text, "Connected to Atlas", .63, .67),
        ]
        for icon, title, value, caption, rx, ry in cards:
            self._floating_card(visual, icon, title, value, caption).place(relx=rx, rely=ry, anchor="nw")

        prompt = ctk.CTkFrame(visual, fg_color="#07102A", corner_radius=25, border_width=1, border_color="#4055A5")
        prompt.place(relx=.49, rely=.90, relwidth=.53, height=56, anchor="center")
        ctk.CTkLabel(prompt, text="✦", text_color="#8EA7FF", font=("Segoe UI Symbol", 16, "bold")).pack(side="left", padx=(15, 7))
        self.dashboard_input = ctk.CTkEntry(prompt, placeholder_text=f"What would you like to explore today, {name}?", fg_color="transparent", border_width=0, height=42, text_color="#F4F7FF", placeholder_text_color="#7180A8", font=self._font(9))
        self.dashboard_input.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(prompt, text="→", width=42, height=42, corner_radius=21, fg_color="#657BFF", hover_color="#8B5CF6", text_color="#FFFFFF", font=self._font(14, "bold"), command=self._dashboard_ask).pack(side="right", padx=5, pady=5)
        self.dashboard_input.bind("<Return>", lambda _e: self._dashboard_ask())
        self._draw_atlas_core()
        self._animate_core()

    def _floating_card(self, parent, title, value, caption):
        frame = ctk.CTkFrame(parent, fg_color=self._c("surface"), corner_radius=17,
                             border_width=1, border_color=self._c("border"))
        ctk.CTkLabel(frame, text=title, text_color=self._c("accent"),
                     font=self._font(7, "bold")).pack(anchor="w", padx=14, pady=(11, 2))
        ctk.CTkLabel(frame, text=value, text_color=self._c("text"),
                     font=self._font(9, "bold"), wraplength=185, justify="left").pack(anchor="w", padx=14)
        ctk.CTkLabel(frame, text=caption, text_color=self._c("muted"),
                     font=self._font(6)).pack(anchor="w", padx=14, pady=(2, 10))
        return frame

    def _quick_action(self, parent, icon, title, caption, command):
        row = ctk.CTkButton(
            parent, text=f"{icon}   {title}\n        {caption}", command=command,
            anchor="w", height=58, fg_color="transparent",
            hover_color=self._c("surface_hover"), text_color=self._c("text"),
            corner_radius=14, font=self._font(9, "bold")
        )
        row.pack(fill="x", padx=10, pady=2)

    def _draw_atlas_core(self):
        canvas = self.core_canvas
        canvas.delete("all")
        w = max(canvas.winfo_width(), 850)
        h = max(canvas.winfo_height(), 650)
        cx, cy = w*.49, h*.46
        max_r = min(w, h)*.24
        for ratio, fill in [(1.65, "#070D25"), (1.38, "#0B1232"), (1.12, "#11154A"), (.90, "#15165B"), (.72, "#1C176A")]:
            r = max_r*ratio
            canvas.create_oval(cx-r, cy-r*.72, cx+r, cy+r*.72, fill=fill, outline="")
        for ratio, width, outline in [(1.62,1,"#243B83"), (1.35,1,"#5269D5"), (1.08,2,"#667BFF"), (.90,1,"#8B5CF6"), (.70,2,"#3B56C4")]:
            r = max_r*ratio
            canvas.create_oval(cx-r, cy-r*.52, cx+r, cy+r*.52, outline=outline, width=width)
        canvas.create_arc(cx-max_r*1.65, cy-max_r*.78, cx+max_r*1.65, cy+max_r*.78, start=12, extent=155, style="arc", outline="#667BFF", width=2)
        canvas.create_arc(cx-max_r*1.45, cy-max_r*1.02, cx+max_r*1.45, cy+max_r*1.02, start=188, extent=150, style="arc", outline="#8B5CF6", width=2)
        core_r = max_r*.56
        for ratio, fill in [(1.18,"#2639A0"),(1.00,"#263BBA"),(.80,"#18296F"),(.61,"#101B4B")]:
            r = core_r*ratio
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=fill, outline="#5D7DFF" if ratio==1.0 else "")
        canvas.create_oval(cx-core_r*.78, cy-core_r*.78, cx+core_r*.78, cy+core_r*.78, outline="#B4C0FF", width=2)
        canvas.create_arc(cx-core_r*.98, cy-core_r*.98, cx+core_r*.98, cy+core_r*.98, start=215, extent=205, style="arc", outline="#B58CFF", width=3)
        canvas.create_text(cx, cy, text="A", fill="#FFFFFF", font=("Segoe UI", max(32,int(core_r*.72)), "bold"))
        canvas.create_text(cx, cy+core_r+28, text="ATLAS CORE", fill="#7382B7", font=self._font(7, "bold"))
        for scale, yoff in [(1.15,.92),(.86,1.08),(.60,1.20)]:
            rw=max_r*scale; ry=max_r*.13; yy=cy+max_r*yoff
            canvas.create_oval(cx-rw, yy-ry, cx+rw, yy+ry, outline="#263B83", width=1)
        self._core_center=(cx,cy,max_r)
        self._core_angle=getattr(self,"_core_angle",0.0)
        self._core_orbits=[]
        for idx,radius in enumerate((max_r*.82,max_r*1.12,max_r*1.42)):
            item=canvas.create_oval(0,0,0,0,fill="#9AA8FF",outline="#596FFF")
            self._core_orbits.append((item,radius,idx))

    def _animate_core(self):
        try:
            if not hasattr(self, "core_canvas") or not self.core_canvas.winfo_exists():
                return
            import math
            canvas = self.core_canvas
            cx, cy, _ = self._core_center
            self._core_angle += .018
            for item, radius, idx in self._core_orbits:
                angle = self._core_angle * (1.0 + idx * .37) + idx * 2.1
                x = cx + radius * math.cos(angle)
                y = cy + radius * .55 * math.sin(angle)
                r = 4 if idx != 1 else 5
                canvas.coords(item, x-r, y-r, x+r, y+r)
            self.after(40, self._animate_core)
        except tk.TclError:
            return

    def _dashboard_ask(self):
        entry = getattr(self, "dashboard_input", None)
        if entry is None:
            return
        query = entry.get().strip()
        if not query:
            return
        self.show_chat()
        self.chat_input.insert(0, query)
        self.send_chat()

    def toggle_theme(self):
        if self.ui.get("theme", "dark") == "dark":
            self.ui["theme"] = "light"
            for key, value in LIGHT_OVERRIDES.items():
                self.ui[key] = value
        else:
            self.ui["theme"] = "dark"
            for key in LIGHT_OVERRIDES:
                self.ui[key] = DEFAULT_UI[key]
        save_ui(self.ui)
        self._apply_window()
        self._build_shell()
        page = getattr(self, "current_page", "home")
        if page == "chat": self.show_chat()
        elif page == "voice": self.show_voice()
        elif page == "learning": self.show_learning()
        elif page == "memory": self.show_memory()
        elif page == "goals": self.show_goals()
        elif page == "knowledge": self.show_notes()
        elif page == "self": self.show_self()
        else: self.show_home()

    def show_learning(self):
        self.current_page = "learning"
        self.set_active("Learning")
        self.clear()
        snap = self._snapshot()
        intel = snap.get("intelligence", {}) if isinstance(snap, dict) else {}
        weak = intel.get("weak_topics", []) if isinstance(intel, dict) else []
        self.header("Learning", "Build your tomorrow", "Adaptive learning evidence, revision and next steps.")
        panel = self.card(self.main)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 28))
        if not weak:
            ctk.CTkLabel(panel, text="No weak-topic evidence yet.", text_color=self._c("text"),
                         font=self._font(18, "bold")).pack(anchor="w", padx=25, pady=(28, 5))
            ctk.CTkLabel(panel, text="Ask Atlas a question or start a practice session to build evidence.",
                         text_color=self._c("muted"), font=self._font(9)).pack(anchor="w", padx=25)
        else:
            ctk.CTkLabel(panel, text="NEXT AREAS TO WORK ON", text_color=self._c("accent"),
                         font=self._font(8, "bold")).pack(anchor="w", padx=25, pady=(25, 12))
            for item in weak[:6]:
                row = ctk.CTkFrame(panel, fg_color=self._c("surface_2"), corner_radius=15)
                row.pack(fill="x", padx=22, pady=5)
                ctk.CTkLabel(row, text=f"{item.get('subject')} · {item.get('topic')}",
                             text_color=self._c("text"), font=self._font(10, "bold")).pack(side="left", padx=14, pady=13)
                ctk.CTkLabel(row, text=f"evidence {item.get('evidence', 0)}",
                             text_color=self._c("muted"), font=self._font(8)).pack(side="right", padx=14)
        self.button(panel, "Ask Atlas what to do next", self.show_chat, 210, True).pack(anchor="w", padx=22, pady=20)

    def show_goals(self):
        self.current_page = "goals"
        self.set_active("Goals")
        self.clear()
        self.header("Goals", "Turn plans into reality", "Keep the goals Atlas is actually tracking in view.")
        panel = self.card(self.main)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 28))
        goals = (self._snapshot().get("intelligence", {}) or {}).get("goals", [])
        if not goals:
            ctk.CTkLabel(panel, text="No active goals yet.", text_color=self._c("text"),
                         font=self._font(20, "bold")).pack(anchor="w", padx=25, pady=(35, 5))
            ctk.CTkLabel(panel, text="Create a goal through Atlas and it will appear here.",
                         text_color=self._c("muted"), font=self._font(9)).pack(anchor="w", padx=25)
        else:
            for goal in goals:
                row = ctk.CTkFrame(panel, fg_color=self._c("surface_2"), corner_radius=15)
                row.pack(fill="x", padx=22, pady=5)
                status = "DONE" if goal.get("done") else "ACTIVE"
                ctk.CTkLabel(row, text=status, text_color=self._c("success") if goal.get("done") else self._c("accent"),
                             font=self._font(8, "bold"), width=65).pack(side="left", padx=12, pady=13)
                ctk.CTkLabel(row, text=goal.get("goal", "Goal"), text_color=self._c("text"),
                             font=self._font(10, "bold")).pack(side="left", padx=5)

    def show_self(self):
        self.current_page = "self"
        self.set_active("Self")
        self.clear()
        profile = self._profile()
        self.header("Self", "Understand yourself", "Your saved student profile, without inventing anything.")
        panel = self.card(self.main)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 28))
        fields = [
            ("NAME", profile.get("name") or "Not set"),
            ("CLASS", profile.get("class") or profile.get("grade") or "Not set"),
            ("SCHOOL", profile.get("school") or "Not set"),
            ("LEARNING PREFERENCE", profile.get("learning_preference") or "Not set"),
        ]
        for label, value in fields:
            row = ctk.CTkFrame(panel, fg_color=self._c("surface_2"), corner_radius=15)
            row.pack(fill="x", padx=22, pady=5)
            ctk.CTkLabel(row, text=label, text_color=self._c("accent"),
                         font=self._font(7, "bold"), width=150, anchor="w").pack(side="left", padx=14, pady=13)
            ctk.CTkLabel(row, text=str(value), text_color=self._c("text"),
                         font=self._font(10, "bold"), anchor="w").pack(side="left", padx=8)

    def show_chat(self):
        self.current_page = "chat"
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
        self.current_page = "voice"
        self.set_active("Voice"); self.clear(); self.header("Voice Core", "Talk, don't type.", "Atlas can listen, reason and respond through the same brain.")
        panel = self.card(self.main, self._c("surface"), 28); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28))
        ctk.CTkLabel(panel, text="✦", text_color=self._c("accent"), font=("Segoe UI Symbol", 110, "bold")).pack(pady=(80, 5))
        ctk.CTkLabel(panel, text="ATLAS IS LISTENING FOR YOU", text_color=self._c("text"), font=self._font(18, "bold")).pack()
        self.voice_status = ctk.CTkLabel(panel, text="READY · LOCAL VOICE" if VOICE_AVAILABLE else "VOICE ENGINE UNAVAILABLE", text_color=self._c("success") if VOICE_AVAILABLE else self._c("danger"), font=self._font(9, "bold")); self.voice_status.pack(pady=8)
        self.voice_hint = ctk.CTkLabel(panel, text="Press once, speak normally, and Atlas will answer.", text_color=self._c("muted"), font=self._font(10)); self.voice_hint.pack()
        self.listen_btn = self.button(panel, "◉  START LISTENING", self.start_voice, 230, True, 48); self.listen_btn.pack(pady=25)

    def start_voice(self):
        if self.voice_busy: return
        if not VOICE_AVAILABLE: self.voice_status.configure(text="VOICE ENGINE UNAVAILABLE", text_color=self._c("danger")); return
        self.voice_busy = True; self.listen_btn.configure(state="disabled", text="◉  LISTENING…"); self.voice_status.configure(text="LISTENING", text_color=self._c("accent")); threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        try:
            text = listen()
            if not text: raise RuntimeError("I didn't hear anything.")
            self.after(0, lambda: self.voice_status.configure(text="THINKING…")); answer = process(text); self.after(0, lambda: self.voice_status.configure(text="SPEAKING…", text_color=self._c("success"))); speak(answer); self.after(0, lambda: self._voice_done("READY · LOCAL VOICE", "Ready for your next question."))
        except Exception as exc: self.after(0, lambda e=str(exc): self._voice_done("VOICE ERROR", e))

    def _voice_done(self, status, hint):
        self.voice_busy = False; self.voice_status.configure(text=status, text_color=self._c("success") if "READY" in status else self._c("danger")); self.voice_hint.configure(text=hint); self.listen_btn.configure(state="normal", text="◉  START LISTENING")

    def show_subject(self, subject):
        self.current_page = "subject"
        self.set_active("Maths" if subject == "Mathematics" else subject); self.clear(); self.header(subject, f"Your {subject} space", "A focused place to understand, practice and improve.")
        grid = ctk.CTkFrame(self.main, fg_color="transparent"); grid.pack(fill="both", expand=True, padx=45, pady=(0, 28)); grid.grid_columnconfigure((0,1), weight=1); grid.grid_rowconfigure((0,1), weight=1)
        cards = [("01", "UNDERSTAND", "Learn the idea from first principles.", lambda: self.open_subject_chat(subject, "Teach me the key concepts")), ("02", "RECALL", "Build a compact formula and concept sheet.", lambda: self.open_subject_chat(subject, "Give me the important formulas and explain them")), ("03", "PRACTICE", "Use questions to turn knowledge into skill.", self.show_practice), ("04", "FIX WEAK SPOTS", "Ask Atlas what needs attention next.", lambda: self.open_subject_chat(subject, "What should I revise and practice next?"))]
        for i, (num, title, desc, cmd) in enumerate(cards):
            c = self.card(grid); c.grid(row=i//2, column=i%2, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(c, text=num, text_color=self._c("accent"), font=self._font(9, "bold")).pack(anchor="w", padx=25, pady=(25, 8)); ctk.CTkLabel(c, text=title, text_color=self._c("text"), font=self._font(20, "bold")).pack(anchor="w", padx=25); ctk.CTkLabel(c, text=desc, text_color=self._c("muted"), font=self._font(10), wraplength=450, justify="left").pack(anchor="w", padx=25, pady=(7, 20)); self.button(c, "Open  →", cmd, 115, True).pack(anchor="w", padx=25, pady=(0, 25))

    def open_subject_chat(self, subject, prompt):
        self.show_chat(); self.chat_input.insert(0, f"{subject}: {prompt}"); self.chat_input.focus()

    def show_notes(self):
        self.current_page = "knowledge"
        self.set_active("Notes"); self.clear(); self.header("Knowledge", "Your study shelf", "Capture explanations, summaries and useful discoveries.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0, 28)); toolbar = ctk.CTkFrame(panel, fg_color="transparent"); toolbar.pack(fill="x", padx=20, pady=18); self.button(toolbar, "＋  New note", self.new_note, 125, True).pack(side="left"); self.button(toolbar, "Open PDF", self.import_pdf, 110).pack(side="left", padx=8); self.notes_box = ctk.CTkTextbox(panel, fg_color=self._c("surface_2"), text_color=self._c("text"), font=self._font(11), wrap="word"); self.notes_box.pack(fill="both", expand=True, padx=20, pady=(0,20)); self.notes_box.insert("1.0", "Your notes live here.\n\nUse Chat to understand a concept, then save the useful part here.")

    def new_note(self): self.notes_box.delete("1.0", "end"); self.notes_box.insert("1.0", f"# Study Note — {datetime.now():%d %b %Y}\n\n")

    def import_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path: return
        if not ingest_pdf: messagebox.showerror("Atlas Library", "PDF ingestion is unavailable."); return
        messagebox.showinfo("Atlas Library", "PDF import is available through the education library.")

    def show_practice(self):
        self.current_page = "practice"
        self.set_active("Practice"); self.clear(); self.header("Practice Lab", "Turn knowledge into skill", "Choose a subject and let Atlas generate the next useful challenge.")
        panel = self.card(self.main); panel.pack(fill="both", expand=True, padx=45, pady=(0,28)); ctk.CTkLabel(panel, text="WHAT DO YOU WANT TO PRACTICE?", text_color=self._c("accent"), font=self._font(9,"bold")).pack(anchor="w", padx=28, pady=(28,7)); ctk.CTkLabel(panel, text="Pick a subject", text_color=self._c("text"), font=self._font(24,"bold")).pack(anchor="w", padx=28); row=ctk.CTkFrame(panel,fg_color="transparent"); row.pack(anchor="w", padx=23, pady=24)
        for s in ["Physics","Mathematics","Chemistry"]: self.button(row,s,lambda x=s:self.open_subject_chat(x,"Give me one practice question at an appropriate difficulty."),160,s=="Physics").pack(side="left", padx=5)

    def show_planner(self):
        self.current_page = "planner"
        self.set_active("Planner"); self.clear(); self.header("Planning", "Your study rhythm", "A simple plan that keeps the important things moving.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=45,pady=(0,28));
        for time_,task in [("16:00","Tuition"),("20:00","Physics · focused study"),("20:45","Mathematics · practice"),("21:30","Chemistry · review")]:
            row=ctk.CTkFrame(panel,fg_color=self._c("surface_2"),corner_radius=14); row.pack(fill="x",padx=25,pady=6); ctk.CTkLabel(row,text=time_,text_color=self._c("accent"),font=self._font(10,"bold"),width=75).pack(side="left",padx=14,pady=14); ctk.CTkLabel(row,text=task,text_color=self._c("text"),font=self._font(10,"bold")).pack(side="left")
        self.button(panel,"Ask Atlas to build a plan",lambda:self.open_subject_chat("Study","Build me a focused study plan."),220,True).pack(anchor="w",padx=25,pady=22)

    def show_memory(self):
        self.current_page = "memory"
        self.set_active("Memory"); self.clear(); self.header("Long-term memory", "What Atlas remembers", "Inspect the durable information connected to your learning.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=45,pady=(0,28)); box=ctk.CTkTextbox(panel,fg_color=self._c("surface_2"),text_color=self._c("text"),font=self._font(10)); box.pack(fill="both",expand=True,padx=20,pady=20)
        try:
            facts=self.memory.get_facts() if self.memory else {}; important=self.memory.get_important_memories() if self.memory else []; lines=["FACTS",""]+[f"• {k}: {v}" for k,v in facts.items()]+["","IMPORTANT MEMORIES",""]+[f"• {x}" for x in important]; box.insert("1.0", "\n".join(lines) if any(lines[2:]) else "No durable memories saved yet.")
        except Exception as exc: box.insert("1.0", f"Memory interface unavailable: {exc}")
        box.configure(state="disabled")

    def show_progress(self):
        self.current_page = "progress"
        self.set_active("Progress"); self.clear(); self.header("Learning analytics", "See your momentum", "Progress should tell you what to do next — not just show numbers.")
        panel=self.card(self.main); panel.pack(fill="both",expand=True,padx=45,pady=(0,28)); data=self.progress.data() if self.progress else {}; signals=data.get("learning_signals",[]) if isinstance(data,dict) else []
        ctk.CTkLabel(panel,text=f"{len(signals)} learning signals recorded",text_color=self._c("muted"),font=self._font(10)).pack(anchor="w",padx=26,pady=(25,18))
        for s,v in [("Physics",.72),("Mathematics",.81),("Chemistry",.76)]: self._progress_row(panel,s,v)

    def _progress_row(self,parent,subject,value):
        row=ctk.CTkFrame(parent,fg_color="transparent"); row.pack(fill="x",padx=26,pady=8); ctk.CTkLabel(row,text=subject,text_color=self._c("text"),font=self._font(10,"bold")).pack(side="left"); ctk.CTkLabel(row,text=f"{int(value*100)}%",text_color=self._c("muted"),font=self._font(9)).pack(side="right"); b=ctk.CTkProgressBar(parent,height=7,progress_color=self._c("accent"),fg_color=self._c("border")); b.pack(fill="x",padx=26); b.set(value)

    # ---------------- Studio: unlocked after seven days ----------------
    def show_studio(self):
        self.current_page = "studio"
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
