from voice.voice_engine import speak, listen
from memory.history import add_message, get_recent_messages


def run_voice_mode(llm):

    speak("Voice mode activated")

    while True:

        try:

            voice_input = listen()

            if not voice_input:
                continue

            if voice_input.startswith("error"):
                continue

            if voice_input.lower() in [
                "stop voice mode",
                "exit voice mode",
                "voice off",
                "quit"
            ]:
                speak("Voice mode deactivated")
                break

            # Detect Hinglish
            hinglish_words = [
                "kya", "kaise", "kaun", "mera", "meri",
                "tum", "aaj", "kal", "hai", "ho",
                "kyu", "kab", "kitna", "acha", "bura"
            ]

            is_hinglish = any(
                word in voice_input.lower().split()
                for word in hinglish_words
            )

            language_instruction = (
                "Reply in Hinglish (Hindi written in English letters)."
                if is_hinglish
                else "Reply in English."
            )

            add_message("User", voice_input)

            history = get_recent_messages(3)

            history_text = ""

            for msg in history:
                history_text += (
                    f"{msg['role']}: "
                    f"{msg['message']}\n"
                )

            prompt = f"""
You are Atlas, a personal AI assistant created by Ashish.

Rules:
- You are Atlas.
- You were created by Ashish.
- Never identify as Qwen.
- Speak like a smart AI assistant similar to FRIDAY.
- Be friendly, calm, and confident.
- Keep responses short and natural.
- Address the user as Ashish when appropriate.
- Reply in Hinglish if the user speaks Hinglish.
- Reply in English if the user speaks English.
- Avoid long explanations unless asked.

Examples:

User: tumhara naam kya hai
Atlas: Mera naam Atlas hai.

User: aaj weather kaisa hai
Atlas: Main weather check kar sakta hoon agar internet available ho.

User: what is python
Atlas: Python is a popular programming language.

Conversation:
{history_text}

User:
{voice_input}

Atlas:
"""

            response = llm.ask(prompt)

            if not response:
                response = "I could not generate a response."

            response = str(response)

            response = response.replace("Qwen", "Atlas")
            response = response.replace("qwen", "Atlas")
            response = response.replace("Alibaba Cloud", "Ashish")

            add_message("Atlas", response)

            print("Atlas:", response)

            speak(response)

        except Exception as e:

            error_msg = f"Voice mode error: {e}"

            print(error_msg)

            try:
                speak("Sorry, I encountered an error.")
            except:
                pass