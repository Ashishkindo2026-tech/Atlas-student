import speech_recognition as sr
import pyttsx3
import requests

# 🗣️ TEXT TO SPEECH ENGINE
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

def speak(text):
    print("Atlas:", text)
    engine.say(text)
    engine.runAndWait()


# 🎧 SPEECH TO TEXT ENGINE
recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)

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


# 🧠 AI BRAIN CONNECTOR (OLLAMA)
def ask_atlas(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json().get("response", "No response")

    except Exception as e:
        return f"Brain error: {e}"