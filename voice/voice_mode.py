"""Voice mode wired to the same Atlas Student brain as text mode."""
from __future__ import annotations

from brain.agent import process
from voice.voice_engine import listen, speak
from voice.student_voice import StudentVoice
from voice.wake_word import WakeWord


def run_voice_mode(_llm=None):
    voice = StudentVoice(processor=process, speaker=speak)
    wake = WakeWord()
    active = False
    speak("Atlas Student voice mode activated. Say Hey Atlas to begin.")
    while True:
        try:
            text = listen()
            if not text or text.lower().startswith("error"):
                continue
            if text.lower() in {"stop voice mode", "exit voice mode", "voice off", "quit"}:
                speak("Voice mode deactivated")
                break
            if not active:
                matched, command = wake.accept(text)
                if not matched:
                    continue
                active = True
                if command:
                    voice.handle_text(command)
                else:
                    speak("Yes?")
                continue
            voice.handle_text(text)
        except KeyboardInterrupt:
            speak("Voice mode deactivated")
            break
        except Exception as exc:
            print(f"Voice mode error: {exc}")
            speak("Sorry, I encountered a voice error.")
