"""Launch a real, voice-first Atlas Student beta session.

This is intentionally a thin launcher around the existing Atlas voice stack.
It does not create fake answers or simulate a student. The student speaks to
Atlas and Atlas responds through the local LLM/voice engine.
"""

from llm.ollama_client import Ollama_Client
from voice.voice_mode import run_voice_mode
from education.library_watcher import scan_and_ingest


def start_beta() -> None:
    print("=" * 56)
    print("ATLAS STUDENT — REAL BETA v0.1")
    print("Voice-first student session")
    print("=" * 56)
    print("Before starting, make sure Ollama is running locally.")
    print("Put authorized NCERT PDFs in ncert_books/ if you want source retrieval.")
    print()

    try:
        imported = scan_and_ingest()
        successful = [item for item in imported if "error" not in item]
        failed = [item for item in imported if "error" in item]
        print(f"[EDUCATION] Library scan complete: {len(successful)} book(s) ready.")
        for item in failed:
            print(f"[EDUCATION ERROR] {item.get('path', 'unknown')}: {item['error']}")
    except Exception as exc:
        print(f"[EDUCATION WARNING] {type(exc).__name__}: {exc}")

    try:
        llm = Ollama_Client()
    except Exception as exc:
        print(f"[LLM ERROR] {type(exc).__name__}: {exc}")
        print("Start Ollama and run this command again.")
        raise SystemExit(1)

    print()
    print("REAL BETA SESSION")
    print("Try this sequence naturally:")
    print('  1. "Explain Newton\'s third law for my Class 11 exam."')
    print('  2. "Give me one example."')
    print('  3. "I still don\'t understand it."')
    print("Then continue with your own questions.")
    print('Say "stop voice mode" when you are finished.')
    print()

    run_voice_mode(llm)


if __name__ == "__main__":
    start_beta()
