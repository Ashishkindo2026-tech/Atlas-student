import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_engine import listen, speak, ask_atlas

WAKE_WORD = "hey atlas"

def main():
    speak("Atlas voice system online")

    while True:
        text = listen()

        if not text:
            continue

        # 🛑 EXIT
        if "exit" in text or "stop" in text:
            speak("Shutting down voice system")
            break

        # 🎯 WAKE WORD DETECTION
        if WAKE_WORD in text:
            speak("Yes?")

            command = listen()

            if not command:
                speak("I didn't hear anything")
                continue

            # 🧠 GET RESPONSE FROM BRAIN
            response = ask_atlas(command)

            if not response:
                speak("No response received")
            else:
                speak(response)


if __name__ == "__main__":
    main()