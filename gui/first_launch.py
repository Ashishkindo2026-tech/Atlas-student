"""First-launch personalization wizard for Atlas Student.

The first time Atlas starts, the student chooses how their Atlas should look.
The choices are stored locally and reused by the Learning OS. The wizard can
also be launched again with ``--setup`` from the desktop launcher.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
UI_FILE = APPDATA / "ui.json"
SETUP_FILE = APPDATA / "first_launch_complete"

DEFAULTS = {
    "background": "#080A0F",
    "sidebar": "#06080C",
    "panel": "#10141B",
    "panel_alt": "#141923",
    "panel_hover": "#1A202C",
    "text": "#F4F6FA",
    "muted": "#8993A5",
    "accent": "#86A4FF",
    "accent_hover": "#A8BAFF",
    "accent_dark": "#263554",
    "success": "#70D2A5",
    "warning": "#E6B86A",
    "danger": "#E58D8D",
    "border": "#252C39",
    "font": "Segoe UI",
    "font_size": 10,
    "title_size": 29,
    "radius": 18,
    "sidebar_width": 230,
    "ui_scale": 1.0,
    "opacity": 1.0,
    "animation_ms": 200,
    "show_sidebar": True,
    "show_status": True,
    "show_date": True,
    "background_image": "",
    "background_image_opacity": 1.0,
    "layout": "learning_os",
}

PRESETS = {
    "Atlas": {"accent": "#86A4FF", "accent_hover": "#A8BAFF", "accent_dark": "#263554"},
    "Midnight": {"accent": "#B58CFF", "accent_hover": "#D0B6FF", "accent_dark": "#3A285C", "background": "#09070F", "panel": "#120F1B"},
    "Ocean": {"accent": "#55C7E8", "accent_hover": "#91E2F4", "accent_dark": "#1D4656", "background": "#061016", "panel": "#0C1720"},
    "Mint": {"accent": "#63D8B0", "accent_hover": "#9AE8CF", "accent_dark": "#21483D", "background": "#070D0C", "panel": "#0F1715"},
    "Ember": {"accent": "#FF9A6A", "accent_hover": "#FFC09D", "accent_dark": "#5C3020", "background": "#100907", "panel": "#1A100D"},
}


def load_existing() -> dict:
    data = deepcopy(DEFAULTS)
    try:
        if UI_FILE.exists():
            raw = json.loads(UI_FILE.read_text(encoding="utf-8"))
            data.update({k: v for k, v in raw.items() if k in data})
    except Exception:
        pass
    return data


def save_ui(data: dict) -> None:
    APPDATA.mkdir(parents=True, exist_ok=True)
    UI_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    SETUP_FILE.write_text("Atlas personalization completed.\n", encoding="utf-8")


def needs_setup() -> bool:
    return not SETUP_FILE.exists()


class AtlasFirstLaunch(ctk.CTk):
    """Interactive first-launch designer with live preview."""

    def __init__(self, initial: dict | None = None):
        super().__init__()
        self.ui = initial or load_existing()
        self.title("ATLAS — Make it yours")
        self.geometry("1180x760")
        self.minsize(980, 680)
        self.configure(fg_color=self.ui["background"])
        self.step = 0
        self._build()

    def _font(self, size, weight="normal"):
        return (self.ui["font"], int(size * self.ui["ui_scale"]), weight)

    def _build(self):
        outer = ctk.CTkFrame(self, fg_color=self.ui["background"], corner_radius=0)
        outer.pack(fill="both", expand=True)
        left = ctk.CTkFrame(outer, fg_color=self.ui["sidebar"], corner_radius=0, width=410)
        left.pack(side="left", fill="both", expand=False)
        left.pack_propagate(False)
        ctk.CTkLabel(left, text="◉", text_color=self.ui["accent"], font=("Segoe UI Symbol", 42, "bold")).pack(anchor="w", padx=42, pady=(48, 8))
        ctk.CTkLabel(left, text="ATLAS", text_color=self.ui["text"], font=self._font(30, "bold")).pack(anchor="w", padx=42)
        ctk.CTkLabel(left, text="YOUR PERSONAL LEARNING SYSTEM", text_color=self.ui["muted"], font=self._font(9, "bold")).pack(anchor="w", padx=44, pady=(2, 34))
        ctk.CTkLabel(left, text="Let's make Atlas yours.", text_color=self.ui["text"], font=self._font(24, "bold"), wraplength=310, justify="left").pack(anchor="w", padx=42)
        ctk.CTkLabel(left, text="Before you start learning, choose how you want your Atlas to look. You can change everything later in Atlas Studio.", text_color=self.ui["muted"], font=self._font(11), wraplength=315, justify="left").pack(anchor="w", padx=42, pady=(10, 24))
        self.step_label = ctk.CTkLabel(left, text="01  •  LOOK", text_color=self.ui["accent"], font=self._font(9, "bold")); self.step_label.pack(anchor="w", padx=42, pady=(18, 5))
        ctk.CTkLabel(left, text="Your choices are saved locally on this computer.", text_color=self.ui["muted"], font=self._font(9), wraplength=300, justify="left").pack(anchor="w", padx=42)

        right = ctk.CTkFrame(outer, fg_color=self.ui["background"], corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        self.content = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=34, pady=28)
        self.preview = ctk.CTkFrame(right, fg_color=self.ui["panel"], corner_radius=self.ui["radius"], border_width=1, border_color=self.ui["border"], width=360, height=210)
        self.preview.place(relx=0.95, rely=0.95, anchor="se", relwidth=0.40, relheight=0.29)
        self._render_page()

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _render_page(self):
        self._clear_content()
        self.step_label.configure(text=["01  •  LOOK", "02  •  COLOR", "03  •  LAYOUT", "04  •  FINISH"][self.step])
        if self.step == 0:
            self._page_look()
        elif self.step == 1:
            self._page_color()
        elif self.step == 2:
            self._page_layout()
        else:
            self._page_finish()
        self._render_preview()

    def _heading(self, eyebrow, title, subtitle):
        ctk.CTkLabel(self.content, text=eyebrow.upper(), text_color=self.ui["accent"], font=self._font(9, "bold")).pack(anchor="w", pady=(8, 3))
        ctk.CTkLabel(self.content, text=title, text_color=self.ui["text"], font=self._font(28, "bold")).pack(anchor="w")
        ctk.CTkLabel(self.content, text=subtitle, text_color=self.ui["muted"], font=self._font(10), wraplength=560, justify="left").pack(anchor="w", pady=(5, 22))

    def _choice_button(self, parent, title, description, command, selected=False):
        frame = ctk.CTkFrame(parent, fg_color=self.ui["accent_dark"] if selected else self.ui["panel"], corner_radius=self.ui["radius"], border_width=1, border_color=self.ui["accent"] if selected else self.ui["border"])
        frame.pack(fill="x", pady=6)
        button = ctk.CTkButton(frame, text=title, command=command, anchor="w", fg_color="transparent", hover_color=self.ui["panel_hover"], text_color=self.ui["text"], font=self._font(11, "bold"), height=44)
        button.pack(fill="x", padx=8, pady=(7, 0))
        ctk.CTkLabel(frame, text=description, text_color=self.ui["muted"], font=self._font(9), wraplength=510, justify="left").pack(anchor="w", padx=20, pady=(0, 10))

    def _page_look(self):
        self._heading("Personalize", "How do you want your Atlas to feel?", "Choose a starting style. Nothing here is permanent — every setting can be changed later.")
        for name, description in [("Calm & Focused", "Minimal panels, quiet contrast and a distraction-free study atmosphere."), ("Futuristic", "Sharper Atlas Core accents and a more technical personal-computer feel."), ("Minimal", "Less visual noise, smaller panels and a clean study workspace.")]:
            self._choice_button(self.content, name, description, lambda n=name: self._choose_layout(n), self.ui.get("layout") == name.lower().replace(" ", "_"))
        self._heading("Theme", "Pick a starting palette", "You can choose your exact colors on the next step.")
        row = ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", pady=4)
        for name in PRESETS:
            ctk.CTkButton(row, text=name, command=lambda n=name: self._preset(n), fg_color=PRESETS[name]["accent"], hover_color=PRESETS[name]["accent_hover"], text_color=PRESETS[name].get("background", "#080A0F"), width=92, height=38, corner_radius=12, font=self._font(9, "bold")).pack(side="left", padx=4)

    def _choose_layout(self, name):
        self.ui["layout"] = name.lower().replace(" & ", "_").replace(" ", "_")
        if name == "Minimal":
            self.ui["sidebar_width"] = 200; self.ui["radius"] = 12; self.ui["animation_ms"] = 140
        elif name == "Futuristic":
            self.ui["sidebar_width"] = 250; self.ui["radius"] = 18; self.ui["animation_ms"] = 220
        else:
            self.ui["sidebar_width"] = 230; self.ui["radius"] = 18; self.ui["animation_ms"] = 200
        self._render_page()

    def _preset(self, name):
        self.ui.update(PRESETS[name]); self._render_page()

    def _page_color(self):
        self._heading("Visual identity", "Make the colors yours", "Pick the colors that define your Atlas. Use the color picker or paste a hex value.")
        for key, label in [("background", "Background"), ("panel", "Main panels"), ("sidebar", "Sidebar"), ("accent", "Atlas accent"), ("accent_hover", "Accent highlight"), ("text", "Main text"), ("muted", "Muted text"), ("border", "Borders")]:
            row = ctk.CTkFrame(self.content, fg_color=self.ui["panel"], corner_radius=12); row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, text_color=self.ui["text"], font=self._font(10, "bold"), width=150, anchor="w").pack(side="left", padx=14, pady=10)
            sw = ctk.CTkButton(row, text=self.ui[key], fg_color=self.ui[key], hover_color=self.ui[key], width=130, command=lambda k=key: self._pick(k)); sw.pack(side="right", padx=10)

        row = ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", pady=8)
        ctk.CTkLabel(row, text="Background image", text_color=self.ui["text"], font=self._font(10, "bold")).pack(side="left")
        ctk.CTkButton(row, text="Choose image", command=self._pick_background, fg_color=self.ui["panel_hover"], hover_color=self.ui["accent_dark"]).pack(side="right")

    def _pick(self, key):
        chosen = colorchooser.askcolor(color=self.ui[key], title=f"Atlas — Choose {key}")[1]
        if chosen:
            self.ui[key] = chosen.upper(); self._render_page()

    def _pick_background(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")])
        if path: self.ui["background_image"] = path; self._render_page()

    def _page_layout(self):
        self._heading("Workspace", "Choose your Atlas layout", "Decide how much of the interface you want visible while you study.")
        for key, label, description in [("show_sidebar", "Show navigation sidebar", "Keep subjects, Chat, Voice, Memory, Progress and Studio one click away."), ("show_status", "Show Atlas Core status", "Display the ONLINE / CORE status indicator."), ("show_date", "Show date", "Keep the date visible in the Atlas header.")]:
            row = ctk.CTkFrame(self.content, fg_color=self.ui["panel"], corner_radius=12); row.pack(fill="x", pady=6)
            ctk.CTkLabel(row, text=label, text_color=self.ui["text"], font=self._font(10, "bold")).pack(side="left", padx=16, pady=15)
            switch = ctk.CTkSwitch(row, text="", progress_color=self.ui["accent"], button_color=self.ui["text"], command=lambda k=key, s=None: None)
            switch.pack(side="right", padx=16); switch.select() if self.ui[key] else switch.deselect(); switch.configure(command=lambda k=key, s=switch: self._toggle(k, s))
        self._slider("UI scale", "ui_scale", 0.85, 1.25, 0.01)
        self._slider("Window opacity", "opacity", 0.80, 1.0, 0.01)
        self._slider("Corner radius", "radius", 8, 28, 1)
        self._slider("Sidebar width", "sidebar_width", 190, 320, 1)

    def _toggle(self, key, switch): self.ui[key] = bool(switch.get()); self._render_preview()

    def _slider(self, label, key, low, high, step):
        row = ctk.CTkFrame(self.content, fg_color="transparent"); row.pack(fill="x", pady=7)
        ctk.CTkLabel(row, text=label, text_color=self.ui["text"], font=self._font(10, "bold"), width=150, anchor="w").pack(side="left")
        value = ctk.CTkLabel(row, text=str(self.ui[key]), text_color=self.ui["muted"], width=60); value.pack(side="right")
        scale = ctk.CTkSlider(row, from_=low, to=high, number_of_steps=max(1, int((high-low)/step)), progress_color=self.ui["accent"], command=lambda v, k=key, l=value, st=step: self._set_slider(k, v, l, st))
        scale.set(float(self.ui[key])); scale.pack(side="left", fill="x", expand=True, padx=8)

    def _set_slider(self, key, value, label, step):
        self.ui[key] = round(float(value), 2 if step < 1 else 0); label.configure(text=str(self.ui[key])); self._render_preview()

    def _page_finish(self):
        self._heading("Ready", "This is your Atlas", "Save your choices. Atlas will open with this design every time, and Atlas Studio will let you change it whenever you want.")
        summary = ctk.CTkFrame(self.content, fg_color=self.ui["panel"], corner_radius=self.ui["radius"]); summary.pack(fill="x", pady=10)
        for label, value in [("Palette", self.ui["accent"]), ("Font", self.ui["font"]), ("Sidebar", "Visible" if self.ui["show_sidebar"] else "Hidden"), ("Background", "Custom image" if self.ui["background_image"] else "Atlas surface")]:
            row = ctk.CTkFrame(summary, fg_color="transparent"); row.pack(fill="x", padx=18, pady=7); ctk.CTkLabel(row, text=label, text_color=self.ui["muted"], font=self._font(9)).pack(side="left"); ctk.CTkLabel(row, text=value, text_color=self.ui["text"], font=self._font(10, "bold")).pack(side="right")
        ctk.CTkLabel(self.content, text="You can reopen this experience later with the setup option, or use Atlas Studio for deeper control.", text_color=self.ui["muted"], font=self._font(9), wraplength=560, justify="left").pack(anchor="w", pady=16)

    def _render_preview(self):
        self.preview.configure(fg_color=self.ui["panel"], border_color=self.ui["accent"], corner_radius=int(self.ui["radius"]))
        for child in self.preview.winfo_children(): child.destroy()
        ctk.CTkLabel(self.preview, text="◉  ATLAS CORE  •  ONLINE", text_color=self.ui["accent"], font=self._font(9, "bold")).pack(anchor="w", padx=18, pady=(14, 6))
        ctk.CTkLabel(self.preview, text="Your Atlas", text_color=self.ui["text"], font=self._font(18, "bold")).pack(anchor="w", padx=18)
        ctk.CTkLabel(self.preview, text="Chat  •  Voice  •  Learning  •  Studio", text_color=self.ui["muted"], font=self._font(9)).pack(anchor="w", padx=18, pady=(2, 12))
        bar = ctk.CTkProgressBar(self.preview, progress_color=self.ui["accent"], fg_color=self.ui["border"], height=7); bar.pack(fill="x", padx=18); bar.set(.78)
        ctk.CTkLabel(self.preview, text="LIVE PREVIEW", text_color=self.ui["muted"], font=self._font(8, "bold")).pack(anchor="e", padx=18, pady=(8, 0))

    def _next(self):
        if self.step < 3:
            self.step += 1; self._render_page(); return
        self.finish()

    def _back(self):
        if self.step > 0:
            self.step -= 1; self._render_page()

    def finish(self):
        save_ui(self.ui)
        self.destroy()

    def run(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.place(relx=0.50, rely=0.96, anchor="s", relwidth=0.48)
        back = ctk.CTkButton(nav, text="← Back", command=self._back, width=110, fg_color=self.ui["panel_hover"], hover_color=self.ui["accent_dark"], text_color=self.ui["text"])
        back.pack(side="left")
        next_text = lambda: "Finish & Start Atlas" if self.step == 3 else "Continue  →"
        self.next_button = ctk.CTkButton(nav, text=next_text(), command=self._next, width=180, fg_color=self.ui["accent"], hover_color=self.ui["accent_hover"], text_color=self.ui["background"], font=self._font(10, "bold"))
        self.next_button.pack(side="right")
        self._update_nav = lambda: self.next_button.configure(text=next_text())
        self.mainloop()


def run_first_launch(force: bool = False) -> bool:
    if not force and not needs_setup():
        return False
    wizard = AtlasFirstLaunch()
    wizard.run()
    return True


if __name__ == "__main__":
    run_first_launch(force=True)
