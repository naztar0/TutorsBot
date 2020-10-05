from asyncio import sleep
import time
import json


async def check():
    while True:
        with open('chats.json', 'r') as f:
            data = json.load(f)
        expired = []
        for chat in data:
            if data[chat]['created'] < time.time() - 605000:  # one week
                expired.append(chat)
        for chat in expired:
            del data[chat]
        with open('chats.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        await sleep(70000)
