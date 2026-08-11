from ollama import chat

response = chat(
    model="qwen2.5:1.5b",
    messages=[
        {
            "role": "user",
            "content": "Who are you?"
        }
    ]
)

print(response["message"]["content"])