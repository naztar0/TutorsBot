from asyncio import sleep
import time
import json


async def check():
    while True:
        with open('temp_chats.json', 'r') as f:
            temp_chats = json.load(f)
        with open('chats.json', 'r') as f:
            chats = json.load(f)
        expired = []
        for chat in temp_chats:
            if temp_chats[chat]['created'] < time.time() - 1800:  # 30 minutes
                expired.append(chat)
        if expired:
            for chat in expired:
                del temp_chats[chat]
                if chats.get(chat):
                    del chats[chat]
            with open('temp_chats.json', 'w', encoding='utf-8') as f:
                json.dump(temp_chats, f, indent=2)
            with open('chats.json', 'w', encoding='utf-8') as f:
                json.dump(chats, f, indent=2)
        await sleep(60)
