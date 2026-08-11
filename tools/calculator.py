import requests

class Ollama_Client:
    def __init__(self, model="qwen2.5:1.5b"):
        self.model = model

    def ask(self, prompt):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )

            response.raise_for_status()
            return response.json().get("response", "No response from model.")

        except Exception as e:
            return f"Error: {e}"