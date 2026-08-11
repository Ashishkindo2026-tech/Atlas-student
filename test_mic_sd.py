import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

duration = 5
samplerate = 16000

print("Speak now...")

audio = sd.rec(
    int(duration * samplerate),
    samplerate=samplerate,
    channels=1,
    dtype="int16"
)

sd.wait()

sf.write("temp.wav", audio, samplerate)

print("Recording saved.")

r = sr.Recognizer()

with sr.AudioFile("temp.wav") as source:
    data = r.record(source)

try:
    text = r.recognize_google(data)
    print("You said:", text)

except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR:", repr(e))