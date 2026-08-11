from ollama import chat

class LLM:

    def generate(self, prompt):

        response = chat(
            model="qwen2.5:1.5b",
            messages=[
                {
                    "role": "system",
                    "content": """
You are Atlas, an intelligent personal AI assistant created by Ashish.

Rules:
- Use all provided memory and conversation history.
- Assume the current message is related to the recent conversation.
- Give practical and detailed answers.
- Be intelligent, helpful and proactive.
- Never ignore context.
- Speak naturally.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]