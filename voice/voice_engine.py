"""Atlas voice input/output with graceful online/offline degradation."""
import asyncio
import os
import tempfile
import time

import edge_tts
import pygame
import speech_recognition as sr

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


def _recognize_offline(audio):
    """Try SpeechRecognition's local Sphinx backend without network access."""
    try:
        return recognizer.recognize_sphinx(audio).strip()
    except (sr.UnknownValueError, sr.RequestError, AttributeError):
        return ""


def listen():
    """Return recognized text, preferring local STT and falling back online."""
    try:
        with sr.Microphone() as source:
            print("[VOICE] Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return ""

            # Local recognition first: Atlas remains useful without internet.
            local_text = _recognize_offline(audio)
            if local_text:
                print("You (offline):", local_text)
                return local_text

            # Online fallback when the optional local Sphinx engine/model is absent
            # or cannot decode the sample.
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
