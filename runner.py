from yahoosports import getGame
from openNote import makeNote, writeNote
import asyncio

async def main():
    headline, gameSum = await getGame()
    note_hwnd = makeNote()
    writeNote(note_hwnd, f"Headline: {headline}\nGame Summary: {gameSum}")
    return headline, gameSum


if __name__ == "__main__":
    asyncio.run(main())