"""Atlas Student desktop launcher.

The implementation lives in ``gui.learning_os`` so the UI engine can evolve
independently from this stable entry point.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.learning_os import AtlasGUI, main

__all__ = ["AtlasGUI", "main"]


if __name__ == "__main__":
    main()
