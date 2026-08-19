print("VOICE ENGINE FROM VOICE FOLDER LOADED")
import asyncio
import os
import time

import edge_tts
import pygame
import speech_recognition as sr

from llm.ollama_client import Ollama_Client


# Shared LLM client: voice must use the same reliability path as text mode.
_llm = Ollama_Client()


# 🎤 TEXT TO SPEECH (FRIDAY-STYLE VOICE)
def speak(text):
    print("USING SONIA VOICE")
    try:
        print("Atlas:", text)
        file = "atlas_voice.mp3"

        async def generate():
            communicate = edge_tts.Communicate(str(text), "en-GB-SoniaNeural")
            await communicate.save(file)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate())
        finally:
            loop.close()

        pygame.mixer.init()
        try:
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        finally:
            pygame.mixer.quit()

        if os.path.exists(file):
            os.remove(file)

    except Exception as e:
        print("TTS ERROR:", e)
        try:
            if os.path.exists(file):
                os.remove(file)
        except OSError:
            pass


# 🎧 SPEECH TO TEXT
recognizer = sr.Recognizer()


def listen():
    try:
        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
                text = recognizer.recognize_google(audio)
                print("You:", text)
                return text.lower()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return ""
    except Exception as e:
        print("VOICE INPUT ERROR:", e)
        return f"error: {e}"


# 🧠 OLLAMA CONNECTOR
# Kept for compatibility with existing callers; the implementation is now
# centralized in llm.ollama_client instead of maintaining a second HTTP path.
def ask_atlas(prompt):
    return _llm.ask(prompt)
