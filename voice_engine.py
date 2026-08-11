import speech_recognition as sr
import pyttsx3

# 🎙️ ATLAS FEMALE VOICE ENGINE
# Prefer a female Windows voice automatically. If a female voice is not
# installed, keep the system default rather than crashing.
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)


def _select_female_voice():
    voices = engine.getProperty("voices") or []
    preferred = ("zira", "hazel", "heera", "susan", "female", "aria", "jenny")

    for voice in voices:
        name = (getattr(voice, "name", "") or "").lower()
        voice_id = (getattr(voice, "id", "") or "").lower()
        if any(word in name or word in voice_id for word in preferred):
            engine.setProperty("voice", voice.id)
            return voice

    # Some Windows SAPI voices expose gender metadata.
    for voice in voices:
        gender = str(getattr(voice, "gender", "")).lower()
        if "female" in gender:
            engine.setProperty("voice", voice.id)
            return voice

    return None


SELECTED_VOICE = _select_female_voice()


def speak(text):
    print("Atlas:", text)
    engine.say(str(text))
    engine.runAndWait()


# 🎧 SPEECH-TO-TEXT ENGINE
recognizer = sr.Recognizer()


def listen():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.4)

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
            return f"error: {e}"
