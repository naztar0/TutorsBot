from asyncio import sleep
import time
import json
import os


async def check():
    while True:
        with open('chats.json', 'r') as f:
            data = json.load(f)
        expired = []
        for chat in data:
            if data[chat]['created'] < time.time() - 1209600:  # two weeks
                expired.append(chat)
        for chat in expired:
            del data[chat]
            try: os.remove(f'export/media/{chat}.txt')
            except FileNotFoundError: pass
            try: os.remove(f'export/text/{chat}.txt')
            except FileNotFoundError: pass
        with open('chats.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        await sleep(70000)
