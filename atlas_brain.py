import requests

MODEL = "qwen2.5:1.5b"

def ask_atlas(prompt):
    url = "http://localhost:11434/api/generate"

    data = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    return response.json()["response"]

while True:
    user_input = input("\nYou: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break

    reply = ask_atlas(user_input)
    print("\nAtlas:", reply)