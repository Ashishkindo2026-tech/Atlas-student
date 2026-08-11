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

            data = response.json()

            return data.get(
                "response",
                "No response."
            )

        except Exception as e:

            return f"Error: {e}"