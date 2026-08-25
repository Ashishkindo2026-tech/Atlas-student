"""Atlas Visual Customization Studio.

A standalone local editor for the Atlas Learning OS visual system. It edits the
GUI theme constants in gui/atlas_gui.py without touching learning logic.
"""
from __future__ import annotations

import re
from pathlib import Path
from tkinter import colorchooser, messagebox

import customtkinter as ctk

ROOT = Path(__file__).resolve().parents[1]
GUI_FILE = ROOT / "gui" / "atlas_gui.py"

FIELDS = [
    ("Background", "BG"),
    ("Sidebar / Rail", "RAIL"),
    ("Panel", "PANEL"),
    ("Secondary Panel", "PANEL_2"),
    ("Button / Card", "PANEL_3"),
    ("Main Text", "TEXT"),
    ("Muted Text", "MUTED"),
    ("Atlas Accent", "ACCENT"),
    ("Accent Highlight", "ACCENT_2"),
    ("Active Accent", "ACCENT_DARK"),
    ("Success", "SUCCESS"),
    ("Warning", "WARNING"),
    ("Danger", "DANGER"),
    ("Borders", "BORDER"),
]

PRESETS = {
    "Atlas Default": {
        "BG":"#080A0F","RAIL":"#06080C","PANEL":"#10141B","PANEL_2":"#141923","PANEL_3":"#1A202C",
        "TEXT":"#F4F6FA","MUTED":"#8993A5","ACCENT":"#86A4FF","ACCENT_2":"#A8BAFF","ACCENT_DARK":"#263554",
        "SUCCESS":"#70D2A5","WARNING":"#E6B86A","DANGER":"#E58D8D","BORDER":"#252C39",
    },
    "Midnight Violet": {
        "BG":"#09070F","RAIL":"#06040A","PANEL":"#120F1B","PANEL_2":"#181421","PANEL_3":"#211B2D",
        "TEXT":"#F7F2FF","MUTED":"#9D91AD","ACCENT":"#B58CFF","ACCENT_2":"#D0B6FF","ACCENT_DARK":"#3A285C",
        "SUCCESS":"#72D6AE","WARNING":"#E9BE72","DANGER":"#E98D9C","BORDER":"#2D253A",
    },
    "Graphite Mint": {
        "BG":"#070D0C","RAIL":"#050908","PANEL":"#0F1715","PANEL_2":"#141F1C","PANEL_3":"#1B2925",
        "TEXT":"#F1F8F5","MUTED":"#8D9E98","ACCENT":"#63D8B0","ACCENT_2":"#9AE8CF","ACCENT_DARK":"#21483D",
        "SUCCESS":"#70D2A5","WARNING":"#E6B86A","DANGER":"#E58D8D","BORDER":"#263631",
    },
    "Deep Ocean": {
        "BG":"#061016","RAIL":"#040A0F","PANEL":"#0C1720","PANEL_2":"#12212C","PANEL_3":"#192C39",
        "TEXT":"#F0F8FC","MUTED":"#8EA4B1","ACCENT":"#55C7E8","ACCENT_2":"#91E2F4","ACCENT_DARK":"#1D4656",
        "SUCCESS":"#70D2A5","WARNING":"#E6B86A","DANGER":"#E58D8D","BORDER":"#243945",
    },
}


def read_theme() -> dict[str, str]:
    text = GUI_FILE.read_text(encoding="utf-8")
    result = {}
    for _label, key in FIELDS:
        match = re.search(rf'^{key}\\s*=\\s*["\'](#[0-9A-Fa-f]{{6}})["\']', text, re.MULTILINE)
        result[key] = match.group(1) if match else "#000000"
    return result


def write_theme(values: dict[str, str]) -> None:
    text = GUI_FILE.read_text(encoding="utf-8")
    for _label, key in FIELDS:
        value = values[key].upper()
        text, count = re.subn(
            rf'^{key}\\s*=\\s*["\']#[0-9A-Fa-f]{{6}}["\']',
            f'{key} = "{value}"', text, count=1, flags=re.MULTILINE,
        )
        if count != 1:
            raise RuntimeError(f"Could not update theme variable: {key}")
    GUI_FILE.write_text(text, encoding="utf-8")


class AtlasCustomizer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ATLAS — Visual Customization Studio")
        self.geometry("900x720")
        self.minsize(760, 620)
        self.configure(fg_color="#080A0F")
        self.values = read_theme()
        self.swatches: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="ATLAS", text_color=self.values["ACCENT"], font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=32, pady=(28, 2))
        ctk.CTkLabel(self, text="Visual Customization Studio", text_color=self.values["TEXT"], font=("Segoe UI", 30, "bold")).pack(anchor="w", padx=32)
        ctk.CTkLabel(self, text="Edit the entire Atlas visual language. Changes affect the desktop GUI only — learning data and logic stay untouched.", text_color=self.values["MUTED"], wraplength=800, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=32, pady=(5, 20))

        toolbar = ctk.CTkFrame(self, fg_color="transparent"); toolbar.pack(fill="x", padx=32, pady=(0, 12))
        ctk.CTkLabel(toolbar, text="PRESETS", text_color=self.values["MUTED"], font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 8))
        self.preset = ctk.CTkOptionMenu(toolbar, values=list(PRESETS), command=self.apply_preset, width=190); self.preset.pack(side="left")
        ctk.CTkButton(toolbar, text="Reset to Default", command=lambda: self.apply_preset("Atlas Default"), width=130).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self, fg_color="#10141B", corner_radius=16); scroll.pack(fill="both", expand=True, padx=32, pady=(0, 18))
        for row, (label, key) in enumerate(FIELDS):
            line = ctk.CTkFrame(scroll, fg_color="transparent"); line.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(line, text=label, text_color=self.values["TEXT"], font=("Segoe UI", 10, "bold"), width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(line, text=key, text_color=self.values["MUTED"], width=100, anchor="w").pack(side="left")
            swatch = ctk.CTkButton(line, text=self.values[key], fg_color=self.values[key], hover_color=self.values[key], width=150, height=34, command=lambda k=key: self.pick(k))
            swatch.pack(side="right")
            self.swatches[key] = swatch

        bottom = ctk.CTkFrame(self, fg_color="transparent"); bottom.pack(fill="x", padx=32, pady=(0, 24))
        ctk.CTkButton(bottom, text="Cancel", command=self.destroy, width=120).pack(side="right", padx=6)
        ctk.CTkButton(bottom, text="Save Theme to Atlas", command=self.save, width=190, fg_color=self.values["ACCENT"], text_color="#080A0F").pack(side="right", padx=6)
        ctk.CTkLabel(bottom, text="Restart Atlas after saving to apply the new theme.", text_color=self.values["MUTED"], font=("Segoe UI", 9)).pack(side="left")

    def pick(self, key: str):
        chosen = colorchooser.askcolor(color=self.values[key], title=f"Choose {key}")
        if chosen and chosen[1]:
            self.values[key] = chosen[1].upper()
            self._refresh_swatch(key)

    def _refresh_swatch(self, key: str):
        self.swatches[key].configure(text=self.values[key], fg_color=self.values[key], hover_color=self.values[key])

    def apply_preset(self, name: str):
        self.values.update(PRESETS[name])
        for _label, key in FIELDS:
            self._refresh_swatch(key)

    def save(self):
        try:
            write_theme(self.values)
            messagebox.showinfo("Atlas", "Theme saved successfully. Restart Atlas to apply it.")
        except Exception as exc:
            messagebox.showerror("Atlas", f"Could not save theme:\n{exc}")


if __name__ == "__main__":
    AtlasCustomizer().mainloop()
