"""Atlas voice I/O with local-first STT/TTS and graceful degradation."""
import asyncio
import os
import tempfile
import time

import edge_tts
import pygame
import speech_recognition as sr

try:
    import pyttsx3
except ImportError:  # Optional until dependencies are installed.
    pyttsx3 = None

recognizer = sr.Recognizer()


def _speak_local(text):
    """Use the operating system's local TTS engine when available."""
    if pyttsx3 is None:
        return False
    try:
        engine = pyttsx3.init()
        engine.say(str(text))
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as exc:
        print("[VOICE/LOCAL-TTS DEGRADED]", type(exc).__name__)
        return False


def speak(text):
    """Speak text locally first; use online neural TTS only as a fallback."""
    if _speak_local(text):
        return

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


def _recognize_offline(audio):
    """Use the bundled local Sphinx backend; never contacts the network."""
    try:
        return recognizer.recognize_sphinx(audio).strip()
    except (sr.UnknownValueError, sr.RequestError, AttributeError):
        return ""


def listen():
    """Recognize speech locally first, with an optional online fallback."""
    try:
        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                return ""

            local_text = _recognize_offline(audio)
            if local_text:
                print("You (offline):", local_text)
                return local_text

            try:
                text = recognizer.recognize_google(audio)
                print("You (online):", text)
                return text.strip()
            except (sr.UnknownValueError, sr.RequestError) as exc:
                print("[VOICE/STT DEGRADED]", type(exc).__name__)
                return ""
    except Exception as exc:
        print("[VOICE INPUT DEGRADED]", type(exc).__name__, exc)
        return ""
