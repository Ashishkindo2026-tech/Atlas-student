"""Atlas voice input/output with graceful degradation."""
import asyncio
import os
import time

import edge_tts
import pygame
import speech_recognition as sr

from llm.ollama_client import Ollama_Client


_llm = Ollama_Client()


def speak(text):
    """Speak text when TTS is available; never crash Atlas on audio failure."""
    file = "atlas_voice.mp3"
    try:
        print("Atlas:", text)

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
    except Exception as exc:
        print("[VOICE/TTS DEGRADED]", type(exc).__name__, exc)
    finally:
        try:
            if os.path.exists(file):
                os.remove(file)
        except OSError:
            pass


recognizer = sr.Recognizer()


def listen():
    """Return recognized text, or an empty string when voice input is unavailable.

    The voice layer must never inject infrastructure error strings into the
    normal Atlas conversation pipeline.
    """
    try:
        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
                text = recognizer.recognize_google(audio)
                print("You:", text)
                return text.lower()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return ""
            except sr.RequestError as exc:
                print("[VOICE/STT DEGRADED] Recognition service unavailable:", exc)
                return ""
    except Exception as exc:
        print("[VOICE INPUT DEGRADED]", type(exc).__name__, exc)
        return ""


def ask_atlas(prompt):
    """Compatibility wrapper using Atlas's shared LLM reliability path."""
    return _llm.ask(prompt)
