print("VOICE ENGINE FROM VOICE FOLDER LOADED")
import speech_recognition as sr
import requests
import asyncio
import edge_tts
import pygame
import os
# 🎤 TEXT TO SPEECH (FRIDAY-STYLE VOICE)
def speak(text):

    print("USING JENNY VOICE")

    try:

        print("Atlas:", text)

        file = "atlas_voice.mp3"

        async def generate():
            communicate = edge_tts.Communicate(
                str(text),
                "en-GB-SoniaNeural"
            )
            await communicate.save(file)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate())
        loop.close()

        pygame.mixer.init()
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pass

        pygame.mixer.quit()

        if os.path.exists(file):
            os.remove(file)

    except Exception as e:

        print("TTS ERROR:", e)


# 🎧 SPEECH TO TEXT

recognizer = sr.Recognizer()


def listen():

    with sr.Microphone() as source:

        print("[VOICE] Listening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )


        try:

            audio = recognizer.listen(
                source,
                timeout=6,
                phrase_time_limit=8
            )

            text = recognizer.recognize_google(audio)

            print("You:", text)

            return text.lower()

        except sr.WaitTimeoutError:
            return ""

        except sr.UnknownValueError:
            return ""

        except Exception as e:
            return f"error: {e}"


# 🧠 OLLAMA CONNECTOR

def ask_atlas(prompt):

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json().get(
            "response",
            "No response"
        )

        return result

    except Exception as e:

        return f"Brain error: {e}"