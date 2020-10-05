#!/usr/bin/env python
import constants as c
from buttons import Buttons
from media_group import media_group
import expited_chats_checker

import json
import time
import datetime
import string
import random
from asyncio import sleep

from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(c.token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Export(StatesGroup): code = State()
class New_chat_tutor(StatesGroup): code = State()
class New_chat_client(StatesGroup): code = State()


class Chat(StatesGroup):
    code = State()
    send = State()


async def start_menu(message: types.Message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.introduction_client)
    key.add(Buttons.introduction_tutor)
    await message.answer("Hey there 👋!\nAre you a student or a tutor?\nPlease press one of the buttons below!", reply_markup=key)


@dp.message_handler(commands=['start'], state=Chat)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start_menu(message)


@dp.message_handler(commands=['start'], state=New_chat_tutor)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start_menu(message)


@dp.message_handler(commands=['start'], state=New_chat_client)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start_menu(message)


@dp.message_handler(commands=['start'], state=Export)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await start_menu(message)


async def _send_message(func, **kwargs):
    try:
        await func(**kwargs)
    except utils.exceptions.BotBlocked: return
    except utils.exceptions.UserDeactivated: return
    except utils.exceptions.ChatNotFound: return
    except utils.exceptions.BadRequest: return 0
    return True


def create_new_code():
    word = random.choice(c.random_words)
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    return f'{word}-{code}'


def save_data(path, name: str = None, text: str = None, data_type: str = None, data: str = None):
    if text:
        with open(f'export/text/{path}.txt', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.strftime(datetime.datetime.now(), "%d.%m / %H:%M")} - '
                    f'{name}:\n{text}\n\n')
    if data:
        with open(f'export/media/{path}.txt', 'a', encoding='utf-8') as f:
            f.write(f'{data_type}/{data}\n')


def _media_group_builder(data, caption=True):
    media = types.MediaGroup()
    first = True
    for photo in data['media']['photo']:
        if first:
            first = False
            if caption:
                media.attach_photo(photo, data['media']['caption'])
            else:
                media.attach_photo(photo)
        else:
            media.attach_photo(photo)
    for video in data['media']['video']:
        if first:
            first = False
            if caption:
                media.attach_photo(video, data['media']['caption'])
            else:
                media.attach_photo(video)
        else:
            media.attach_video(video)
    return media


@dp.message_handler(commands=['start'])
async def message_handler(message: types.Message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.introduction_client)
    key.add(Buttons.introduction_tutor)
    await message.answer("Hey there 👋!\nAre you a student or a tutor?\nPlease press one of the buttons below!", reply_markup=key)


@dp.message_handler(commands=['export'])
async def message_handler(message: types.Message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Export.code.set()
    await message.answer("Send me the chat ID to export", reply_markup=key)


async def tutor_main(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.lad_chat_tutor, Buttons.my_chats_tutor)
    key.add(Buttons.support)
    await message.answer("Choose action", reply_markup=key)


async def client_main(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.lad_chat_client, Buttons.my_chats_client)
    key.add(Buttons.support, Buttons.new_order)
    await message.answer("First of all, relax, because we have your back(Smiley)!\n\n"
                         "If you already have your order ID, click on “Ladchat”.\n\n"
                         "If you want to create a new order, click on “New Order”.\n\n"
                         "Didn't receive an order ID? No worries! Contact our support team and we’ll sort things out.",
                         reply_markup=key)


async def lad_chat_client(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await New_chat_client.code.set()
    await message.answer(
        "Ready for some chit-chat? Simply enter your order ID and you will be connected to the 🕴️anonymous🕴️ chat with your tutor!\n\n"
        "Don't have order ID? 😳 Don't worry just create a new order!\n\n"
        "Didn't receive your order ID? 😬\nContact our support team so we can sort things out.", reply_markup=key)
    # TEMPORARY FUNCTION
    code = create_new_code()
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    chats[code] = {'created': int(time.time())}
    with open('chats.json', 'wt') as f:
        json.dump(chats, f, indent=2)
    await message.answer(f"*New chat code, just for test*:\n`{code}`", parse_mode='Markdown')


async def lad_chat_tutor(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await New_chat_tutor.code.set()
    await message.answer(
        "Please enter your order ID to enter the chat. Do not disclose or ask for any personal information.\n"
        "If you have questions regarding payment or clients conduct please message our support team.\n"
        "Chat will be monitored by our quality assurance specialist.", reply_markup=key)


async def my_chats(message, who_am_i, state):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    inline_key = types.InlineKeyboardMarkup()
    exists = False
    iam = message.chat.id
    for code in chats:
        if chats[code].get(who_am_i) == iam:
            inline_key.add(types.InlineKeyboardButton(code, callback_data=code))
            exists = True
    if not exists:
        await message.answer("You haven't any chats")
        return
    await Chat.code.set()
    await state.update_data({'who_am_i': who_am_i})
    await message.answer("There are all your chats", reply_markup=inline_key)
    await message.answer("Choose the chat", reply_markup=key)


async def chat_answer(callback_query, state):
    who_am_i = 'tutor' if callback_query.data[6:7] == 'c' else 'client'
    code = callback_query.data[7:]
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Chat.send.set()
    await state.update_data({'code': code, 'who_am_i': who_am_i})
    await callback_query.answer()
    await callback_query.message.answer("Now all messages will be send to this interlocutor", reply_markup=key)


@dp.message_handler(content_types=['text'])
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        # TEMPORARY
        await client_main(message)
    elif message.text == Buttons.introduction_tutor:
        await tutor_main(message)
    elif message.text == Buttons.introduction_client:
        await client_main(message)
    elif message.text == Buttons.lad_chat_client:
        await lad_chat_client(message)
    elif message.text == Buttons.lad_chat_tutor:
        await lad_chat_tutor(message)
    elif message.text == Buttons.my_chats_client:
        await my_chats(message, 'client', state)
    elif message.text == Buttons.my_chats_tutor:
        await my_chats(message, 'tutor', state)



@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data[:6] == 'answer':
        await chat_answer(callback_query, state)


@dp.message_handler(content_types=['text'], state=New_chat_client.code)
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        await state.finish()
        await client_main(message)
        return
    code = message.text
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    chat = chats.get(code)
    if chat is None:
        await message.answer("Wrong order ID")
        return
    if chat.get('client'):
        await message.answer("There is another client in this chat")
        return
    chats[code]['client'] = message.chat.id
    with open('chats.json', 'w') as f:
        json.dump(chats, f, indent=2)
    await state.finish()
    await state.update_data({'code': code, 'who_am_i': 'client'})
    await Chat.send.set()
    await message.answer("You are successfully connected to the chat!\n*Now all messages will be send to this interlocutor*\n\n"
                         "_Please wait until you receive a message stating that the tutor is connected to the chat, and only after that write him a message_",
                         parse_mode='Markdown')


@dp.message_handler(content_types=['text'], state=New_chat_tutor.code)
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        await state.finish()
        await tutor_main(message)
        return
    code = message.text
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    chat = chats.get(code)
    if chat is None:
        await message.answer("Wrong chat ID")
        return
    if chat.get('client') is None:
        await message.answer("There are no client in this chat")
        return
    if chat.get('tutor'):
        await message.answer("There is another tutor in this chat")
        return
    chats[code]['tutor'] = message.chat.id
    with open('chats.json', 'w') as f:
        json.dump(chats, f, indent=2)
    await state.finish()
    await state.update_data({'code': code, 'who_am_i': 'tutor'})
    await Chat.send.set()
    await message.answer("You are successfully connected to the chat!")
    await _send_message(bot.send_message, chat_id=chat['client'], text="Your tutor is connected! "
                                                                       "Please use this chat to exclusively discuss your assignment. "
                                                                       "We value your privacy, so please refrain from using any "
                                                                       "personal information or unrelated topics. This chat may be "
                                                                       "monitored for quality assurance. Should you have any "
                                                                       "questions contact our support team. Thanks!")


@dp.message_handler(content_types=['text'], state=Chat.code)
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        data = await state.get_data()
        await state.finish()
        if data['who_am_i'] == 'client':
            await client_main(message)
        else:
            await tutor_main(message)


@dp.callback_query_handler(lambda callback_query: True, state=Chat.code)
async def callback_inline(callback_query: types.CallbackQuery, state: FSMContext):
    code = callback_query.data
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    if not chats.get(code):
        await state.finish()
        await callback_query.answer("ID does not exist!", show_alert=True)
        await client_main(callback_query.message)
        return
    await state.update_data({'code': code})
    await Chat.send.set()
    await callback_query.answer()
    await callback_query.message.answer("Now all messages will be send to this interlocutor")


@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=Chat.send)
async def message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    who_am_i = data.get('who_am_i')
    if message.text == Buttons.back or message.text == '/start' or not who_am_i:
        await state.finish()
        if who_am_i == 'client':
            await client_main(message)
        else:
            await tutor_main(message)
        return
    code = data.get('code')
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    interlocutor = chats.get(code)
    if not interlocutor:
        await message.answer("ID does not exist!")
        await state.finish()
        if who_am_i == 'client':
            await client_main(message)
        else:
            await tutor_main(message)
        return
    if who_am_i == 'client':
        ilr = 'tutor'
    else:
        ilr = 'client'
    interlocutor = interlocutor.get(ilr)
    if not interlocutor:
        await message.answer("No interlocutor in the chat!")
        await state.finish()
        if who_am_i == 'client':
            await client_main(message)
        else:
            await tutor_main(message)
        return
    text = ''
    send = None
    key = None
    name = f'@{message.chat.username}' if message.chat.username else message.chat.id
    state_interlocutor = await state.storage.get_data(chat=interlocutor)
    interlocutor_in_chat = state_interlocutor.get('code')
    if interlocutor_in_chat != code:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton("Answer", callback_data=f"answer{data['who_am_i'][0]}{code}"))
    if message.media_group_id:
        data = await media_group(message, state)
        if data is None: return
        await state.update_data({'media_group': True})
        await state.update_data({'media': {'photo': data['media_group']['photo'],
                                           'video': data['media_group']['video'],
                                           'caption': data['media_group']['caption']}})
        data = await state.get_data()
        photo = data['media']['photo']
        video = data['media']['video']
        text = data['media']['caption']

        media = _media_group_builder(data, caption=True)
        send = await _send_message(bot.send_media_group, chat_id=interlocutor, media=media)

        for p in photo:
            save_data(code, name, text, 'photo', p)
        for v in video:
            save_data(code, name, text, 'video', v)
    elif message.text:
        text = message.text
        send = await _send_message(bot.send_message, chat_id=interlocutor, text=f'{code}:\n{text}', reply_markup=key)
        save_data(code, name, text)
    elif message.photo:
        photo = message.photo[-1].file_id
        if message.caption:
            text = message.caption
        send = await _send_message(bot.send_photo, chat_id=interlocutor, photo=photo, caption=f'{code}:\n{text}', reply_markup=key)
        save_data(code, name, text, 'photo', photo)
    elif message.video:
        video = message.video.file_id
        if message.caption:
            text = message.caption
        send = await _send_message(bot.send_video, chat_id=interlocutor, video=video, caption=f'{code}:\n{text}', reply_markup=key)
        save_data(code, name, text, 'video', video)
    elif message.document:
        file = message.document.file_id
        send = await _send_message(bot.send_document, chat_id=interlocutor, document=file, caption=f'{code}:\n{text}', reply_markup=key)
        save_data(code, name, text, 'document', file)
    if send:
        await message.answer(f"Message sent to the chat `{code}`", parse_mode='Markdown')
    elif send == 0:
        await message.answer("An error occurred. The message text may be too long.")
    else:
        await message.answer("The message wasn't delivered, the user may have blocked the bot")


@dp.message_handler(content_types=['text'], state=Export.code)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == Buttons.back:
        await client_main(message)
        return
    code = message.text
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    if not chats.get(code):
        await message.answer("ID does not exist!")
        await client_main(message)
        return
    try:
        await bot.send_document(message.chat.id, types.InputFile(f'export/text/{code}.txt', f'{code} text messages.txt'))
    except FileNotFoundError:
        await message.answer("There are no text messages")
    await sleep(.05)
    try:
        with open(f'export/media/{code}.txt', 'r') as f:
            data = f.readlines()
        for file in data:
            filetype, fileid = file[:-1].split('/')
            try:
                if filetype == 'photo':
                    await bot.send_photo(message.chat.id, fileid)
                elif filetype == 'video':
                    await bot.send_video(message.chat.id, fileid)
                elif filetype == 'document':
                    await bot.send_document(message.chat.id, fileid)
            except Exception as e:
                await message.answer(str(e))
            await sleep(.05)
    except FileNotFoundError:
        await message.answer("There are no media files")
    await client_main(message)




if __name__ == '__main__':
    dp.loop.create_task(expited_chats_checker.check())
    executor.start_polling(dp, skip_updates=True)
