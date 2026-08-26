"""ATLAS Student desktop launcher.

Atlas starts with a polished default Learning OS instead of interrupting a
student on day one with a customization wizard. After seven days of use, Atlas
offers the student a one-time invitation to open Atlas Studio. ``--setup``
remains available whenever the student wants to customize the interface.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import messagebox

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.first_launch import run_first_launch
from gui.learning_os import main as learning_os_main
from gui.usage_tracker import mark_offer_shown, record_launch, should_offer_customization


def _offer_week_one_customization() -> None:
    """Offer Atlas Studio after the student's first seven days."""
    if not should_offer_customization():
        return

    mark_offer_shown()
    dialog = tk.Tk()
    dialog.withdraw()
    dialog.attributes("-topmost", True)
    try:
        open_studio = messagebox.askyesno(
            "ATLAS — Make it yours",
            "You've been using Atlas for a week!\n\n"
            "Would you like to personalize your Atlas now?\n\n"
            "You can change colors, fonts, background, layout, scale and more.\n"
            "You can also open Studio again whenever you want.",
            parent=dialog,
        )
    finally:
        dialog.destroy()

    if open_studio:
        run_first_launch(force=True)


def main() -> None:
    force_setup = "--setup" in sys.argv[1:]
    record_launch()

    # Explicit --setup always wins. Normal launches stay clean until week one.
    if force_setup:
        run_first_launch(force=True)
    else:
        _offer_week_one_customization()

    learning_os_main()


if __name__ == "__main__":
    main()
