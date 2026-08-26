"""ATLAS Student desktop launcher.

First launch opens the Atlas personalization experience. After the student
chooses their visual style, the Learning OS starts with those preferences.
Use ``--setup`` any time to open the personalization experience again.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.first_launch import run_first_launch
from gui.learning_os import main as learning_os_main


def main() -> None:
    force_setup = "--setup" in sys.argv[1:]
    run_first_launch(force=force_setup)
    learning_os_main()


if __name__ == "__main__":
    main()
