"""Atlas Student entry point for the six-phase subsystem."""
from __future__ import annotations

from brain.agent import process
from student.atlas_student import system


def run() -> None:
    print("Atlas Student — six phases online")
    print("Memory | Reasoning | Vision | Voice | Planning | Privacy")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAtlas Student stopped.")
            return
        if text.lower() in {"exit", "quit", "stop"}:
            print("Atlas Student stopped.")
            return
        if not text:
            continue
        result = system.handle(text)
        if result is None:
            result = process(text)
        print("Atlas:", result)


if __name__ == "__main__":
    run()
