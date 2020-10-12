#!/usr/bin/env python
import constants as c
from buttons import Buttons
from media_group import media_group
import expited_chats_checker
import expited_temp_chats_checker

import json
import time
import datetime
import random
from asyncio import sleep

from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(c.token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Activate(StatesGroup): code = State()
class Export(StatesGroup): code = State()
class Delete(StatesGroup): code = State()
class Settings(StatesGroup): option = State()
class New_chat_tutor(StatesGroup): code = State()
class New_chat_client(StatesGroup): code = State()


class Chat(StatesGroup):
    code = State()
    send = State()


class NewOrder(StatesGroup):
    contact = State()
    subject = State()
    level = State()
    q_type = State()  # short / multiple choice
    m_choice = State()
    s_answers = State()
    timed = State()
    duration = State()
    timezone_city = State()
    additions = State()
    accepting = State()


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


@dp.message_handler(commands=['start'])
async def message_handler(message: types.Message):
    await start_menu(message)


def client_keyboard() -> types.ReplyKeyboardMarkup:
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.my_chats_client, Buttons.new_order)
    key.add(Buttons.support)
    return key


def moderator_keyboard() -> types.ReplyKeyboardMarkup:
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.m_activate, Buttons.m_delete)
    key.add(Buttons.m_export, Buttons.m_show)
    return key


async def start_menu(message: types.Message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.introduction_client)
    key.add(Buttons.introduction_tutor)
    await message.answer("Just a heads up, if the buttons disappear you might want to press the button on the right "
                         "side of your keyboard. Make sure that nothing is typed in.", reply_markup=key)
    await bot.send_animation(message.chat.id, c.instruction_gif)


async def _send_message(func, **kwargs):
    try:
        await func(**kwargs)
    except utils.exceptions.BotBlocked: return
    except utils.exceptions.UserDeactivated: return
    except utils.exceptions.ChatNotFound: return
    except utils.exceptions.BadRequest: return 0
    return True


async def _back_client(message, state):
    if message.text == Buttons.back:
        await state.finish()
        await client_main(message)
        return True
    return


def create_new_code():
    color = random.choice(c.random_colors)
    word = random.choice(c.random_words)
    suffix = random.randint(0, 99)
    return f'{color}{word}{suffix}'


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


def get_price(data) -> float:
    with open('prices.json', 'r') as f:
        prices = json.load(f)

    price: float = 0
    level: str = data['level']
    m_choice: int = data.get('m_choice', 0)
    s_answers: int = data.get('s_answers', 0)
    duration_inc: int = prices['duration_inc'] if data.get('duration') is not None else 0
    questions = m_choice + s_answers
    if questions > 300:
        discount = 0.75
    elif questions > 250:
        discount = 0.71
    elif questions > 200:
        discount = 0.7
    elif questions > 150:
        discount = 0.6
    elif questions > 100:
        discount = 0.5
    elif questions > 50:
        discount = 0.4
    elif questions > 40:
        discount = 0.35
    elif questions > 30:
        discount = 0.25
    elif questions > 20:
        discount = 0.2
    elif questions > 10:
        discount = 0.1
    else:
        discount = 0

    if level == Buttons.level[0]:
        level_multiplier = prices['level_multiplier_1']
    elif level == Buttons.level[1]:
        level_multiplier = prices['level_multiplier_2']
    elif level == Buttons.level[2]:
        level_multiplier = prices['level_multiplier_3']
    else:
        level_multiplier = prices['level_multiplier_4']

    price += m_choice * prices['m_choice']
    price += s_answers * prices['s_answers']
    price *= level_multiplier
    price -= price * discount
    price += duration_inc

    return price.__round__(2)


async def tutor_main(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.my_chats_tutor)
    key.add(Buttons.support)
    await message.answer("Choose action", reply_markup=key)


async def client_main(message):
    await message.answer("First of all, relax, because we have your back 🤓!\n\n"
                         "If you already created an order, click on “MyChats”.\n\n"
                         "If you want to create a new order, click on “New Order”.\n\n"
                         "Didn't receive an order ID? No worries! Contact our support team and we’ll sort things out.",
                         reply_markup=client_keyboard())


async def lad_chat_client(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await New_chat_client.code.set()
    await message.answer(
        "Ready for some chit-chat? Simply enter your order ID and you will be connected to the 🕴️anonymous🕴️ chat with your tutor!\n\n"
        "Don't have order ID? 😳 Don't worry just create a new order!\n\n"
        "Didn't receive your order ID? 😬\nContact our support team so we can sort things out.", reply_markup=key)


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


async def new_order_start(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton("Share contact", request_contact=True))
    await NewOrder.contact.set()
    await message.answer("Please share your contact details with us. This allows our support team to be more efficient "
                         "in helping you. Don't worry your information is only visible to our support specialists.",
                         reply_markup=key)


async def generate_new_chat(callback_query):
    await callback_query.message.edit_reply_markup()
    text = callback_query.data[3:].split('_')
    client = int(text[0])
    price = float(text[1])
    code = create_new_code()
    with open('temp_chats.json', 'r') as f:
        temp_chats = json.load(f)
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    temp_chats[code] = {
        'created': int(time.time()),
        'client': client,
        'tutor': callback_query.from_user.id
    }
    chats[code] = temp_chats[code]
    with open('temp_chats.json', 'w', encoding='utf-8') as f:
        json.dump(temp_chats, f, indent=2)
    with open('chats.json', 'w', encoding='utf-8') as f:
        json.dump(chats, f, indent=2)

    with open('prices.json', 'r') as f:
        prices = json.load(f)
    price_tutor = (price * prices['tutor_share']).__round__(2)

    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton("Pay", url=c.paypal))
    await _send_message(bot.send_message, chat_id=client,
                        text=f"Hey! One of our tutors accepted your order. Your chat ID is: `{code}`\n"
                             f"Please deposit $*{price}* to the following PayPal account. "
                             "Don't forget to add a note with your order id to your payment.\n"
                             "Don't worry you are protected by our money back guarantee as well as PayPals buyer "
                             "protection policy. Your tutor will not get the money until your order is complete.\n\n"
                             "Your chat ID is active but will be deactivated in 30 min if the payment is not made."
                             "Thanks!\n\nTo access your chat click on 'my chats' and then your order ID.",
                        reply_markup=key, parse_mode='Markdown')
    await _send_message(bot.send_message, chat_id=callback_query.from_user.id,
                        text=f"Hey! Your chat ID is: `{code}`\nThe client has 30 min to make a deposit. "
                             f"You will be notified.", parse_mode='Markdown')
    await callback_query.answer("See your private messages with the bot", show_alert=True)

    await bot.send_message(c.moderator_chat, f"*New order!*\n*Chat ID:* `{code}`\n"
                                             f"*Price:* ${price}\n*Tutor share:* ${price_tutor}\n"
                                             f"[Client](tg://user?id={client}) "
                                             f"[Tutor](tg://user?id={callback_query.from_user.id})",
                           parse_mode='Markdown')


async def activate_chat_init(message: types.Message):
    if message.chat.id not in (c.moderator_chat, c.admin_id):
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Activate.code.set()
    await message.answer("Send me the chat ID to activate", reply_markup=key)


async def export_chat_init(message: types.Message):
    if message.chat.id not in (c.moderator_chat, c.admin_id):
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Export.code.set()
    await message.answer("Send me the chat ID to export", reply_markup=key)


async def delete_chat_init(message: types.Message):
    if message.chat.id not in (c.moderator_chat, c.admin_id):
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Delete.code.set()
    await message.answer("Send me the chat ID to delete", reply_markup=key)


async def show_all_chats_init(message: types.Message):
    if message.chat.id not in (c.moderator_chat, c.admin_id):
        return
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    buffer = ''
    for chat in chats:
        buffer += chat + datetime.datetime.strftime(datetime.datetime.fromtimestamp(chats[chat]['created']), "\t- %d.%m / %H:%M\n")
    with open('chats.txt', 'w') as f:
        f.write(buffer)
    await bot.send_document(message.chat.id, types.InputFile('chats.txt'), 'chats.txt')


@dp.message_handler(commands=['settings'])
async def message_handler(message: types.Message):
    if message.chat.id != c.admin_id:
        return
    with open('prices.json', 'r') as f:
        prices = json.load(f)
    buffer = ''
    for option in prices:
        buffer += f'`{option}` - {prices[option]}\n'
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await Settings.option.set()
    await message.answer(buffer + "Send me the option which you want to change with the new value separated by space",
                         parse_mode='Markdown', reply_markup=key)


@dp.message_handler(content_types=['text'])
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        #TEMPORARY
        await client_main(message)
    elif message.text == Buttons.introduction_tutor:
        await tutor_main(message)
    elif message.text == Buttons.introduction_client:
        await client_main(message)
    elif message.text == Buttons.my_chats_client:
        await my_chats(message, 'client', state)
    elif message.text == Buttons.my_chats_tutor:
        await my_chats(message, 'tutor', state)
    elif message.text == Buttons.new_order:
        await new_order_start(message)

    elif message.text == Buttons.m_activate:
        if message.chat.id == c.moderator_chat:
            await activate_chat_init(message)
    elif message.text == Buttons.m_delete:
        if message.chat.id == c.moderator_chat:
            await delete_chat_init(message)
    elif message.text == Buttons.m_export:
        if message.chat.id == c.moderator_chat:
            await export_chat_init(message)
    elif message.text == Buttons.m_show:
        if message.chat.id == c.moderator_chat:
            await show_all_chats_init(message)


@dp.message_handler(content_types=['text'], state=Activate.code)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == Buttons.back:
        await message.answer("Canceled", reply_markup=moderator_keyboard())
        return
    code: str = message.text.lower()
    with open('temp_chats.json', 'r') as f:
        temp_chats = json.load(f)
    chat = temp_chats.get(code)
    if not chat:
        await message.answer("Chat ID does not exist or already activated!", reply_markup=moderator_keyboard())
        return
    del temp_chats[code]
    with open('temp_chats.json', 'w', encoding='utf-8') as f:
        json.dump(temp_chats, f, indent=2)

    with open('chats.json', 'r') as f:
        chats = json.load(f)
    client = chats[code]['client']
    tutor = chats[code]['tutor']
    await _send_message(bot.send_message, chat_id=client, text="We have received the payment, the chat is now fully active!")
    await _send_message(bot.send_message, chat_id=tutor, text="We have received the payment, the chat is now fully active!")
    await message.answer("Activated", reply_markup=moderator_keyboard())


@dp.message_handler(content_types=['text'], state=Export.code)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == Buttons.back:
        await message.answer("Canceled", reply_markup=moderator_keyboard())
        return
    code: str = message.text.lower()
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    if not chats.get(code):
        await message.answer("Chat ID does not exist!", reply_markup=moderator_keyboard())
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
    await message.answer("Sending finished", reply_markup=moderator_keyboard())


@dp.message_handler(content_types=['text'], state=Delete.code)
async def message_handler(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == Buttons.back:

        await message.answer("Canceled", reply_markup=moderator_keyboard())
        return
    code: str = message.text.lower()
    with open('chats.json', 'r') as f:
        chats = json.load(f)
    if not chats.get(code):
        await message.answer("Chat ID does not exist!", reply_markup=moderator_keyboard())
        return
    del chats[code]
    with open('chats.json', 'w', encoding='utf-8') as f:
        json.dump(chats, f, indent=2)
    await message.answer("Chat deleted", reply_markup=moderator_keyboard())


@dp.message_handler(content_types=['text'], state=Settings.option)
async def message_handler(message: types.Message, state: FSMContext):
    if message.text == Buttons.back:
        await state.finish()
        await message.answer("Canceled", reply_markup=client_keyboard())
        return
    text = message.text.split(' ')
    if len(text) != 2:
        await message.answer("Invalid input, please try again", reply_markup=client_keyboard())
        return
    option = text[0]
    value = text[1]
    if not value.isdigit():
        await message.answer("Value is not digit, please try again", reply_markup=client_keyboard())
        return
    await state.finish()
    with open('prices.json', 'r') as f:
        prices = json.load(f)
    prices[option] = float(value)
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(prices, f, indent=2)
    await message.answer("Successfully changed", reply_markup=client_keyboard())


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
        await message.answer("Chat does not exist or has expired!")
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


# New order zone
@dp.message_handler(content_types=['contact'], state=NewOrder.contact)
async def message_handler(message: types.Message, state: FSMContext):
    country_code = str(message.contact.phone_number)[:-9]
    if country_code[0] == '+': country_code = country_code[1:]
    if country_code in c.forbidden_country_codes:
        await state.finish()
        await message.answer("Sorry, your country is not supported")
        await client_main(message)
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.subjects[0], Buttons.subjects[1], Buttons.subjects[2], Buttons.subjects[3], Buttons.subjects[4])
    key.add(Buttons.back)
    await NewOrder.subject.set()
    await message.answer("Please select the subject you need help with:\n"
                         "Math, Stats, Finance, Business, Chem\n\nThanks!", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.subject)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if message.text not in Buttons.subjects:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.level[0], Buttons.level[1], Buttons.level[2])
    key.add(Buttons.back)
    await state.update_data({'subject': message.text})
    await NewOrder.level.set()
    await message.answer("Next, we need to know difficulty level of your assignment. "
                         "If you consider your course to be more or less difficult than "
                         "what our level suggestions are select feel free to select level "
                         "you think best fits your course. However, its crucial that you select "
                         "appropriate difficulty level:\n\nLevel 1: High School\nLevel 2: Undergraduate "
                         "(University Year 1-2) AND IB AP courses.\nLevel 3 Undergraduate (Year 3-4)",
                         reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.level)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if message.text not in Buttons.level:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.q_type[0])
    key.add(Buttons.q_type[1])
    key.add(Buttons.q_type[2])
    key.add(Buttons.back)
    await state.update_data({'level': message.text})
    await NewOrder.q_type.set()
    await message.answer("Next, please tell us what type of questions your assignment has? Please note that we can "
                         "only help with short answers and multiple choice questions.", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.q_type)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if message.text not in Buttons.q_type:
        return
    await state.update_data({'q_type': message.text})
    if message.text == Buttons.q_type[0]:
        await NewOrder.s_answers.set()
        answer = "Ok, how many short answer question does your assignment have? (select 0 if none)"
    else:
        await NewOrder.m_choice.set()
        answer = "How many multiple choice questions does your assignment have? (select 0 if none)"
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await message.answer(answer, reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.m_choice)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if not str(message.text).isdigit():
        return
    data = await state.get_data()
    await state.update_data({'m_choice': int(message.text)})
    if data.get('q_type') == Buttons.q_type[2]:
        await NewOrder.s_answers.set()
        await message.answer("Ok, how many short answer question does your assignment have? (select 0 if none)")
    else:
        if int(message.text) == 0:
            await state.finish()
            await message.answer("So, your assignment doesn't have any questions?")
            return
        else:
            key = types.ReplyKeyboardMarkup(resize_keyboard=True)
            key.add(Buttons.timed[0], Buttons.timed[1])
            key.add(Buttons.back)
            await NewOrder.timed.set()
            await message.answer("Ok, we are almost done!\n\nIs your assignment timed?", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.s_answers)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if not str(message.text).isdigit():
        return
    data = await state.get_data()
    if data.get('q_type') == Buttons.q_type[2]:
        if int(message.text) == 0 and data.get('m_choice') == 0:
            await state.finish()
            await message.answer("So, your assignment doesn't have any questions?")
            return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.timed[0], Buttons.timed[1])
    key.add(Buttons.back)
    await state.update_data({'s_answers': int(message.text)})
    await NewOrder.timed.set()
    await message.answer("Ok, we are almost done!\n\nIs your assignment timed?", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.timed)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if message.text not in Buttons.timed:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    if message.text == Buttons.timed[0]:
        await NewOrder.duration.set()
        await message.answer("How long will you have to complete it?", reply_markup=key)
    else:
        await NewOrder.timezone_city.set()
        await message.answer("When is your assignment due?\nPlease indicate your time zone OR "
                             "city in your answer. For example NYC DD/MM/YY and 8:30 PM", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.duration)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if len(message.text) > 50:
        await message.answer("Too long message, please try again")
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.back)
    await state.update_data({'duration': message.text})
    await NewOrder.timezone_city.set()
    await message.answer("When is your assignment due?\nPlease indicate your time zone OR "
                         "city in your answer. For example NYC DD/MM/YY and 8:30 PM", reply_markup=key)


@dp.message_handler(content_types=['text'], state=NewOrder.timezone_city)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    if len(message.text) > 50:
        await message.answer("Too long message, please try again")
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(Buttons.done)
    key.add(Buttons.back)
    await state.update_data({'timezone_city': message.text})
    await NewOrder.additions.set()
    await message.answer("Finally, is there anything else our tutor should know about your assignment? "
                         "If you have past exams, course outline, sample questions upload them here. "
                         "The more you attach the easier it will be for us to find a tutor that can help you. "
                         "When you are done press DONE.", reply_markup=key)


@dp.message_handler(content_types=['text', 'photo', 'document'], state=NewOrder.additions)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    data = await state.get_data()
    if message.text == Buttons.done:
        price = get_price(data)
        key = types.ReplyKeyboardMarkup(resize_keyboard=True)
        key.add(Buttons.accept)
        key.add(Buttons.support)
        key.add(Buttons.back)
        await state.update_data({'price': price})
        await NewOrder.accepting.set()
        await message.answer(f"Our price for your order is ${price}. If you like it just click accept! "
                             "You won't have to pay until one of our tutors accepts your order.", reply_markup=key)
        return
    elif message.text:
        if len(message.text) > 500:
            await message.answer("Too long message, please try again")
            return
        if len(str(data.get('add_text'))) + len(message.text) > 500:
            await message.answer("The text that has already been sent is too long")
            return
        await state.update_data({'add_text': message.text})
    elif message.photo:
        if message.caption:
            if len(str(data.get('add_text'))) + len(message.caption) > 500:
                await message.answer("The text that has already been sent is too long")
            else:
                await state.update_data({'add_text': message.caption})
        await state.update_data({'add_photo': message.photo[-1].file_id})
    elif message.document:
        await state.update_data({'add_document': message.document.file_id})


@dp.message_handler(content_types=['text'], state=NewOrder.accepting)
async def message_handler(message: types.Message, state: FSMContext):
    if await _back_client(message, state):
        return
    await message.answer("Thanks! We are now looking for a tutor that will match your needs. "
                         "This shouldn't take longer than an hour. While you wait why don't you watch this "
                         "[video](https://youtu.be/ZZb_ZtjVxUQ) of cute puppies🐕!",
                         parse_mode='Markdown', reply_markup=client_keyboard())
    data = await state.get_data()
    await state.finish()

    text = data.get('add_text')
    photo = data.get('add_photo')
    document = data.get('add_document')
    media_links = ''

    if text:
        text_m = await bot.send_message(c.media_chat, text)
        media_links += f'[text](https://t.me/{c.media_chat[1:]}/{text_m.message_id}) '
    if photo:
        photo_m = await bot.send_photo(c.media_chat, photo)
        media_links += f'[photo](https://t.me/{c.media_chat[1:]}/{photo_m.message_id}) '
    if document:
        document_m = await bot.send_document(c.media_chat, document)
        media_links += f'[document](https://t.me/{c.media_chat[1:]}/{document_m.message_id}) '

    with open('prices.json', 'r') as f:
        prices = json.load(f)

    price_tutor = (data['price'] * prices['tutor_share']).__round__(2)
    due_date = data['timezone_city'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[')
    timed = data.get('duration', 'NO').replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[')
    text_to_channel = f"*{data['subject']}*\n" \
                      f"*{data['level']}*\n" \
                      f"*DUE DATE:* {due_date}\n" \
                      f"*TIMED:* {timed}\n" \
                      f"*SHORT ANSWER:* {data.get('s_answers', '0')}\n" \
                      f"*MULTIPLE CHOICE:* {data.get('m_choice', '0')}\n" \
                      f"*ADDITIONAL INFO WITH FILES:* {media_links}\n" \
                      f"*PRICE:* {price_tutor}"

    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton("Take", callback_data=f"new{message.chat.id}_{data['price']}"))

    await bot.send_message(c.tutors_chat, text_to_channel, parse_mode='Markdown', reply_markup=key, disable_web_page_preview=True)


@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data[:6] == 'answer':
        await chat_answer(callback_query, state)
    elif callback_query.data[:3] == 'new':
        await generate_new_chat(callback_query)


@dp.callback_query_handler(lambda callback_query: True, state=Chat)
async def callback_inline(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data[:3] == 'new':
        await state.finish()
        await generate_new_chat(callback_query)





if __name__ == '__main__':
    dp.loop.create_task(expited_chats_checker.check())
    dp.loop.create_task(expited_temp_chats_checker.check())
    executor.start_polling(dp, skip_updates=True)
