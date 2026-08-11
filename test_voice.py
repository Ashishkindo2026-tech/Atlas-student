import asyncio
import edge_tts
import pygame

async def main():

    await edge_tts.Communicate(
        "Hello Ashish. I am Atlas.",
        "en-US-JennyNeural"
    ).save("test.mp3")

asyncio.run(main())

pygame.mixer.init()
pygame.mixer.music.load("test.mp3")
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    pass