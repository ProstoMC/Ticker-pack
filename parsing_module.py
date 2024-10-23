import csv
import datetime
import pytz  # Для UTC времени
import os
import json
import shutil


from constants import tickers, channels
from telethon import TelegramClient

from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl import types

api_id = 26974863
api_hash = 'bc81c358a73e5dd46230a5ba1358e82a'
client = TelegramClient('test_tg', api_id, api_hash)

phone = '79218701469'

utc = pytz.UTC


async def get_messages_from_channel(user_phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if not await client.is_user_authorized():
        print("Client doesn't authorized")
        await client.send_code_request(user_phone)
        try:
            await client.sign_in(password=input('Password: '))
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    # Удаление папки и пересоздание заново для очистки изображений
    if os.path.exists('media'):
        shutil.rmtree('media')
        os.makedirs('media')

    # Подготовка к обновлению
    messages_json = []  # Пустой словарь для сохранения в json файл
    internal_id = 0  # Устанавливаем счетчик в ноль

    for channel in channels:
        # Подготовка к получению данных с канала

        channel_link = channel
        my_channel = await client.get_entity(channel_link)
        print("=== Парсинг канала " + channel + " ===")
        all_messages = []
        offset_id = 0  # Сброшеный id сообщения
        total_messages = 0  # Сброшеный счетчик количества
        offset_date = datetime.datetime.now() - datetime.timedelta(days=1) # Получаем за последние 7 дней - не работает

        total_count_limit = 0  # Ограничение по общему количеству. 0 - нет ограничения
        limit = 10  # Количество полученных сообщений в одной итерации


        # Получаем историю в несколько итераций.
        while True:
            history = await client(GetHistoryRequest(
                peer=my_channel,
                offset_id=offset_id,
                offset_date=offset_date,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                print("===Канал больше не имеет сообщений===")
                break

            messages = history.messages

            for message in messages:

                # Проверяем на наличие картинок, если есть, то скачиваем. В названии канал и id сообщения для нахождения
                media_key = False
                if message.photo:
                    media_key = True
                    path = await client.download_media(message.media, f"media/{internal_id}_{datetime.datetime.now().time().microsecond}")
                    print('File saved to ', path)  # printed after download is done

                # Проверяем есть ли текст в сообщении или только картинка.
                # Только картинку сохраняем с текущим id будущего сообщения
                if message.message != '':
                    # Создание и добавление новой записи в json
                    message_data = {
                        'internal_id': internal_id,
                        'date': message.date.strftime("%Y/%m/%d %H:%M:%S"),
                        'channel_link': channel_link,
                        'message_id': message.id,
                        'text': message.message,
                        'media_key': media_key
                    }
                    messages_json.append(message_data)
                    internal_id = internal_id + 1

                all_messages.append(message)
                offset_id = messages[len(messages) - 1].id
                total_messages = len(all_messages)

            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

            if messages[-1].date < utc.localize(offset_date):
                break



    # Конец перебора каналов и получения сообщений. JSON файл готов

    print("Сохраняем данные в файл...")
    with open('data.json', 'w', encoding="UTF-8") as file:
        json.dump(messages_json, file, ensure_ascii=False)
    print("Парсинг сообщений группы успешно выполнен.")


with client:
    client.loop.run_until_complete(get_messages_from_channel(phone))
