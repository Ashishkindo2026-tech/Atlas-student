import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:1.5b",
        "prompt": "Hello",
        "stream": False
    }
)

print(response.json())