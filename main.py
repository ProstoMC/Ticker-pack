import json
import os
import telebot
from telebot import types  # для указание типов
from  telebot.types import InputMediaPhoto
import parsing_module
from constants import *

token = '883998234:AAH5K0p4hu3K0VqA6p0LGKvwxblH0LlG1Fs'

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Топ-10 акций IMOEX")
    btn2 = types.KeyboardButton("Прогнозы по индексу IMOEX")
    btn3 = types.KeyboardButton("Поиск по тикеру")

    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)

    bot.send_message(message.chat.id,
                     text="Привет, {0.first_name}! Я бот для отслеживания актуальных новостей".format(
                         message.from_user), reply_markup=markup)

#функция для установки главного меню 
def mainKeyboard ():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Топ-10 акций IMOEX")
    btn2 = types.KeyboardButton("Прогнозы по индексу IMOEX")
    btn3 = types.KeyboardButton("Поиск по тикеру")

    keyboard.add(btn1, btn2,btn3)
    return keyboard

#кнопка для возвращения в главное меню
def return_to_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    return_button = types.KeyboardButton("Вернуться в стартовое окно")
    keyboard.add(return_button)
    return keyboard

# Обработка сообщения
@bot.message_handler(content_types=['text'])
def func(message):
    print(message.text)
    if message.text == "Топ-10 акций IMOEX":
        markup = types.InlineKeyboardMarkup()

        for ticker in tickersTop:
            callback = f'show_ticker {ticker}'
            btn = types.InlineKeyboardButton(text=ticker, callback_data=callback)
            markup.add(btn)
        callback = f'return main'

        bot.send_message(message.chat.id, 'Топ-10 акций IMOEX', reply_markup=markup)
    elif message.text == "Прогнозы по индексу IMOEX":
        markup = types.InlineKeyboardMarkup()
        for ticker in tickersMos:
            bot.send_message(message.chat.id, 'Прогноз по индексу ' + ticker, reply_markup=return_to_main_menu_keyboard())
            show_ticker_handler(ticker, message.chat.id)
    elif message.text == "Вернуться в стартовое окно":
       bot.send_message(message.chat.id, "Возврат в стартовое окно", reply_markup=mainKeyboard())
    elif message.text == "Поиск по тикеру":
       bot.send_message(message.chat.id, 'Введите тикер:', reply_markup=return_to_main_menu_keyboard())
    elif len(message.text) == 4:
        bot.send_message(message.chat.id, 'Поиск по тикеру: ' + message.text.upper(), reply_markup=return_to_main_menu_keyboard())
        show_ticker_handler(message.text.upper(), message.chat.id)
    else:
        show_ticker_handler(message.text, message.chat.id) # Выводим сообщения по запросу
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Доступные тикеры")
        markup.add(btn1)
        # bot.send_message(message.chat.id,
        #                  text="Некорректная команда".format(
        #                      message.from_user), reply_markup=markup)


# Обработка колбэков нажатия кнопок
@bot.callback_query_handler(func=lambda call: call.data)
def handle_message(callback):
    print('CALL DATA:' + callback.data)

    if  callback.data.split(" ")[1] in tickers and callback.data.split(" ")[0] == 'show_ticker':
        show_ticker_handler(callback.data.split(" ")[1], callback.message.chat.id)
    #доп. условия для отработки сценария, если нет тикера или нажата кнопка вернуться
    elif 'return' not in callback.data and callback.data.split(" ")[1] not in tickers:
        bot.send_message(callback.message.chat.id, text='Тикера нет в нашей базе :(')
    else:
       bot.send_message(callback.message.chat.id, text='Вернуться в стартовое окно')


# Вспомогательные функции

# Обработка поиска сообщений тикера
def show_ticker_handler(request_str, chat_id):
    max_caption_length = 1024
    print("Поиск строки:" + request_str)
    found_messages, unicChannels = find_messages_by_str(request_str)
    print(f'Количество найденных сообщений: {len(found_messages)}')

    #вывод статистики по поиску
    if len(unicChannels) > 0:
      captionStat = (f'По данному тикеру найдено {len(found_messages)} упоминаний в {len(unicChannels)} каналах. Ниже упоминания из каналов:')
      bot.send_message(chat_id, text=captionStat)


    if not found_messages:
      bot.send_message(chat_id, text="По данному тикеру информации не найдено :(")

    for message in found_messages:
        caption = message.get("text")
        if message.get("media_key", False):
            photo_paths = find_photos_by_message_id(message.get("internal_id"))
            if len(photo_paths) > 1:  # Если больше одного фото
                print("Больше одного фото>")
                photos = []
                for photo_path in photo_paths:
                    photo_file = open(photo_path, 'rb')
                    photos.append(InputMediaPhoto(photo_file))
                if len(caption) > max_caption_length:
                  caption = caption[:max_caption_length]
                photos[0].caption = caption
                try:
                  bot.send_media_group(chat_id, photos)
                except:
                  bot.send_message(chat_id, text=caption)
            else:  # Если только одно фото
                print("ТОЛЬКО ОДНО ФОТО")
                # Отработка ошибки, если фото недоступны 
                try:
                  bot.send_photo(chat_id, open(photo_paths[0], 'rb'), parse_mode='HTML', caption=message.get("text", "Ошибка получения текста"))
                except:
                  bot.send_message(chat_id, text="Фото не прогрузилось")

        else:  # Если только текст
          if len(caption) > max_caption_length:
              caption = caption[:max_caption_length]
          bot.send_message(chat_id, text=caption)


# Поиск сообщений по запросу
def find_messages_by_str(request_str):

    found_messages = []
    unicChannels = []
    messagesDict = {}
    # Выход из функции, если тикера нет в базе
    try:
      searchNames = tickersAddit[request_str]
    except:
      return found_messages, unicChannels

    with open('data.json', "r", encoding='utf-8') as file:
        data = json.load(file)
        for row in data:
            messagesDict[row["internal_id"]] = False
            text = row["text"]
            # Цикл поиска ключевых фраз, связанных с тикером - название компании и тд
            for searchName in searchNames:
              if messagesDict[row["internal_id"]] != True and text is not None and searchName.lower() in text.lower():
                  internal_id = row["internal_id"]
                  channel_link = row["channel_link"]
                  message_id = row["message_id"]
                  media_key = row["media_key"]
                  if row["channel_link"] not in unicChannels:
                    unicChannels.append(row["channel_link"])

                  text = text + "\nИсточник:  " + channel_link

                  message = {"internal_id": internal_id,
                            "channel_link": channel_link,
                            "message_id": message_id,
                            "text": text,
                            "media_key": media_key
                            }
                  found_messages.append(message)
                  messagesDict[row["internal_id"]] = True

    return found_messages, unicChannels #возвращаем сообщения и список уникальных каналов - источников сообщений


# Поиск прикрепленных к сообщению фото
def find_photos_by_message_id(message_id):
    photo_paths = []

    for root, dirs, files in os.walk('./media/'):
        for file in files:
            if file.startswith(f'{message_id}_'):
                path = os.path.join(root, file)
                print(path)
                photo_paths.append(path)
    return photo_paths


bot.polling(none_stop=True)