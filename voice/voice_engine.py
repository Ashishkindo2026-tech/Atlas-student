"""Atlas voice input/output with graceful degradation."""
import asyncio
import os
import tempfile
import time

import edge_tts
import pygame
import speech_recognition as sr


# Optional local STT providers can be added without changing Atlas's voice API.
# The current provider remains the standard SpeechRecognition backend.
recognizer = sr.Recognizer()


def speak(text):
    """Speak text when TTS is available; never crash Atlas on audio failure."""
    fd, file = tempfile.mkstemp(prefix="atlas_voice_", suffix=".mp3")
    os.close(fd)
    try:
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


def listen():
    """Return recognized text or an empty string when voice input is unavailable."""
    try:
        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
                text = recognizer.recognize_google(audio)
                print("You:", text)
                return text.strip()
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return ""
            except sr.RequestError as exc:
                print("[VOICE/STT DEGRADED] Recognition service unavailable:", exc)
                return ""
    except Exception as exc:
        print("[VOICE INPUT DEGRADED]", type(exc).__name__, exc)
        return ""
