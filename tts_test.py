import asyncio
import edge_tts

async def main():
    communicate = edge_tts.Communicate(
        "Namaste Ashish, main Atlas hoon.",
        "hi-IN-SwaraNeural"
    )
    await communicate.save("test.mp3")

asyncio.run(main())

print("Done")