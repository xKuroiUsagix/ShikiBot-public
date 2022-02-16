import logging
import os

from enum import Enum
from flask import Flask, request
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from ShikiParser import ShikiParser
from ShikiParser import TitleNotFoundError, TitleNameFormatError
from ShikiBotDB import CallbackProxy


# Need to add some emojies for this text
START_TEXT = \
"""
Вас привествует Шики-бот!
Я знаю все о Шикимори :)
        
Краткая инстуркция:

- Для поиска аниме отправьте сообщение в формате:
  Аниме *название аниме*

- Для поиска манги отправьте сообщение в формате:
  Манга *название манги*

- Поиск работает как с английскими так и русскими названиями

- Можно использовать только большие/маленькие буквы и цифры

- Ключевые слова не обязательно писать с большой буквы

- Если поиск не нашел то что вы хотели, попробуйте изменить формулировку\
 либо напишите название на английском (к примеру JoJo лучше чем ДжоДжо)

Желаю вам удачного поиска :)

P.S: Бот не является официальным.
"""


# Logging
FORMAT = '[%(asctime)s]   %(levelname)-8s   FILE: %(filename)s    MESSAGE: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT, filename='logs.log')

TITLE_NAME_STARTS = 6  # Position where title starts in message
# New emoji should be defined here
class Emoji(Enum):
    STAR = '\U00002B50'
    CLOUD = '\U0001F4AD'
    CLAPPER_BOARD = '\U0001F3AC'
    CHECKMARK = '\U00002705'
    CROSSMARK = '\U0000274C'

# New error messages should be defined here
class ErrorMessage(Enum):
    NOT_FOUND = 'К сожалению тайтл не найден'
    BAD_NAME = 'Упс, похоже вы ввели не подходящее имя'
    NO_SYNOPSIS = 'Описание отсутсвует'
    NO_SCORE = 'У тайтла пока нет рейтинга'
    NO_GENRES = 'У тайтла не указаны жанры'
    # OUT_OF_DATE = 'Скорее всего время исполнения запроса истекло :('


def get_token():
    """
    Read the token from token.txt
    """
    with open('token.txt') as file:
        return file.read()


TOKEN = get_token()
bot = TeleBot(TOKEN)
server = Flask(__name__)
parser = ShikiParser()


def get_inline_keyboard(callback_id):
    """
    Attributes:
    - title_name {str}: used in callback data
    - is_anime {bool}: used in callback data
    Create and return inline keyboard for title.
    Callback data:
    - chat_id {int}
    - synopsis or score
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton(
            f"{Emoji.CLOUD.value} Описание {Emoji.CLOUD.value}",
            callback_data=f'{callback_id}|synopsis'),
        InlineKeyboardButton(
            f"{Emoji.STAR.value} Рейтинг {Emoji.STAR.value}",
            callback_data=f'{callback_id}|score'),
        InlineKeyboardButton(
            f"{Emoji.CLAPPER_BOARD.value} Жанры {Emoji.CLAPPER_BOARD.value}",
            callback_data=f'{callback_id}|genre'
        )
    ) 
    return markup


def construct_message(title_name, title_info):
    return f'*{title_name}*\n\n{title_info}'


def send_message(chat_id, title_name, title_info, title_error=None):
    if not title_error:
        title_name_check = title_name + f' {Emoji.CHECKMARK.value}'
    else:
        title_name_check = title_name + f' {Emoji.CROSSMARK.value}'

    bot.send_message(chat_id,
                    construct_message(
                        title_name_check,
                        title_info),
                        parse_mode='Markdown'
    )


@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Bot send message with greeting and short instruction "how to"
    """
    bot.send_message(message.chat.id, START_TEXT)


@bot.message_handler(content_type=['text'])
def clear_old_records(message):
    """
    Every time when someone send a message to the bot
    it deletes old records from database
    """
    callback_proxy = CallbackProxy()
    callback_proxy.delete_old_callbacks(hours=1)


@bot.message_handler(content_types=['text'])
def search_title(message):
    """
    Bots react on every message which starts with "аниме" or "манга". 
    Not register sensitive.
    Store user callback in Callbacks DB.
    If anime not found send ErrorMessage.NOT_FOUND
    If anime name format is wrong, send ErrorMessage.BAD_NAME
    """
    message_text = message.text.lower()
    if message_text[:TITLE_NAME_STARTS-1] in ['аниме', 'манга']:
        callback_proxy = CallbackProxy()

        title_name = message.text[TITLE_NAME_STARTS:]
        is_anime = True if message_text.startswith('аниме') else False
        chat_id = message.chat.id

        try:
            title = parser.search_title(title_name, is_anime)
            # Adds callback to db
            callback_id = callback_proxy.add_callback(
                chat_id,
                title.name,
                float(title.score),
                title.synopsis(),
                title.genres
            )
            logging.info(f'Callback for user {chat_id} written to database.')

            keyboard = get_inline_keyboard(callback_id)
            bot.send_photo(
                chat_id,
                title.image_url,
                caption=f'*{title.name}*',
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except TitleNotFoundError:
            bot.send_message(chat_id, f'{ErrorMessage.NOT_FOUND.value} {Emoji.CROSSMARK.value}')
            logging.error(f'Title ({title_name}) not found')
        except TitleNameFormatError:
            bot.send_message(chat_id, f'{ErrorMessage.BAD_NAME.value} {Emoji.CROSSMARK.value}')
            logging.error(f'Title name ({title_name}) wrong format')


@bot.callback_query_handler(func=lambda call: True)
def callback_title(call):
    """
    React on InlineButton click event.
    If button "Описание" clicked - send title synopsis.
    If button "Рейтинг" clicked - send title score.

    If there is no synopsis - send ERROR_MESSAGES['no synopsis']
    If there is no score - send ERROR_MESSAGES['no score']
    """
    callback_proxy = CallbackProxy()

    splitted = call.data.split('|')
    callback_id, button_context = splitted[0], splitted[1]
    callback = callback_proxy.get_callback_by_id(callback_id)
    title_info = ''
    title_error = ''

    if callback is None:
        logging.warning(f'Callback with chat id {callback.chat_id} NOT FOUND')
        return
    if button_context == 'synopsis':
        if callback.title_synopsis:
            title_info = callback.title_synopsis
            logging.info(f'Send ({callback.title_name}) synopsis for user {callback.chat_id}')
        else:
            title_error = ErrorMessage.NO_SYNOPSIS.value
            logging.warning(f'Not found synopsis for ({callback.title_name})')
    if button_context == 'score':
        if callback.title_score:
            title_info = str(callback.title_score) + f' {Emoji.STAR.value}'
            logging.info(f'Send ({callback.title_name}) for user {callback.chat_id}')
        else:
            title_error = ErrorMessage.NO_SCORE.value
            logging.warning(f'Not found score for ({callback.title_name})')
    if button_context == 'genre':
        if callback.title_genres:
            title_info = callback.title_genres
            logging.info(f'Send ({callback.title_name}) genres for user {callback.chat_id}')
        else:
            title_error = ErrorMessage.NO_GENRES.value
            logging.warning(f'Not found genres for ({callback.title_name})')


    send_message(callback.chat_id, callback.title_name, title_info, title_error)



@server.route('/bot', methods=['POST'])
def get_message():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode('utf-8'))])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://shiki-bot.herokuapp.com/bot')
    return '!', 200

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 80)))
    # while True:
    #     try:
    #         bot.polling(none_stop=True)
    #     # It's bad practice but the only way to make bot works forever
    #     except Exception as e:
    #         logging.warning(f'Some unexpected error has occured: {e}')
