"""Canonical local theme storage shared by the wizard, Studio, and Learning OS.

The GUI historically had two slightly different color schemas. This module
normalizes both schemas so a theme selected in one screen is immediately and
persistently understood by every other Atlas UI surface.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "AtlasStudent"
UI_FILE = APPDATA / "ui.json"
SETUP_FILE = APPDATA / "first_launch_complete"

DEFAULT_UI: dict[str, Any] = {
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
    "accent_dark": "#263554",
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
    "background_image": "",
    "background_image_opacity": 1.0,
    "show_sidebar": True,
    "show_status": True,
    "show_date": True,
    "layout": "learning_os",
}

WIZARD_TO_OS = {
    "panel": "surface",
    "panel_alt": "surface_2",
    "panel_hover": "surface_hover",
    "accent_hover": "accent_2",
}

HEX_KEYS = {"background", "background_2", "sidebar", "surface", "surface_2",
            "surface_hover", "text", "muted", "accent", "accent_2", "accent_dark",
            "success", "warning", "danger", "border"}

def _valid_hex(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value[1:])


def normalize_theme(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    data = deepcopy(DEFAULT_UI)
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            target = WIZARD_TO_OS.get(key, key)
            if target not in data:
                continue
            if target in HEX_KEYS and not _valid_hex(value):
                continue
            if target in {"ui_scale", "opacity", "background_image_opacity"}:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
            elif target in {"font_size", "title_size", "radius", "sidebar_width", "animation_ms"}:
                try:
                    value = int(value) if target != "animation_ms" else int(value)
                except (TypeError, ValueError):
                    continue
            data[target] = value
    data["accent_dark"] = data.get("accent_dark") or data["background_2"]
    data["ui_scale"] = max(0.75, min(1.5, float(data["ui_scale"])))
    data["opacity"] = max(0.5, min(1.0, float(data["opacity"])))
    data["background_image_opacity"] = max(0.0, min(1.0, float(data["background_image_opacity"])))
    data["sidebar_width"] = max(180, min(360, int(data["sidebar_width"])))
    data["radius"] = max(8, min(40, int(data["radius"])))
    data["animation_ms"] = max(50, min(800, int(data["animation_ms"])))
    return data


def load_ui() -> dict[str, Any]:
    try:
        raw = json.loads(UI_FILE.read_text(encoding="utf-8")) if UI_FILE.exists() else {}
    except (OSError, json.JSONDecodeError, TypeError):
        raw = {}
    return normalize_theme(raw)


def save_ui(data: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_theme(data)
    APPDATA.mkdir(parents=True, exist_ok=True)
    tmp = UI_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(UI_FILE)
    SETUP_FILE.write_text("Atlas personalization completed.\n", encoding="utf-8")
    return normalized


def import_theme(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    raw = json.loads(source.read_text(encoding="utf-8"))
    return normalize_theme(raw)


def export_theme(path: str | Path, data: Mapping[str, Any] | None = None) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(normalize_theme(data or load_ui()), indent=2, ensure_ascii=False),
                      encoding="utf-8")
    return target
