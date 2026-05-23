import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))

import telebot
from config import TOKEN, URL
from parser import get_page_data
from db import session, User
from telebot import types

bot = telebot.TeleBot(TOKEN)

# Активные поиски: {chat_id: threading.Event}
stop_events = {}


@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Profil")
    item2 = types.KeyboardButton("Produkty")
    markup.add(item1, item2)

    bot.send_message(message.chat.id, "Witaj! Wybierz opcję:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.lower() == "produkty")
def closet_title(message):
    user = session.query(User).filter_by(name=message.from_user.username).first()
    if not user:
        bot.send_message(message.chat.id, 'Najpierw zarejestruj się — kliknij Profil')
        return
    bot.send_message(message.chat.id, 'Napisz nazwę przedmiotu')
    bot.register_next_step_handler(message, closet_price_to)


def closet_price_to(message):
    title = message.text
    bot.send_message(message.chat.id, 'Napisz maksymalną cenę')
    bot.register_next_step_handler(message, closet_price_from, title)


def closet_price_from(message, title):
    price_to = message.text
    bot.send_message(message.chat.id, 'Napisz minimalną cenę')
    bot.register_next_step_handler(message, start_search, title, price_to)


def start_search(message, title, price_to):
    price_from = message.text

    url = (URL + "%20".join(title.split()) +
           '&order=newest_first' +
           f'&price_to={price_to}' +
           f'&price_from={price_from}' +
           '&currency=PLN')

    chat_id = message.chat.id

    # Останавливаем предыдущий поиск для этого чата, если есть
    if chat_id in stop_events:
        stop_events[chat_id].set()

    stop_event = threading.Event()
    stop_events[chat_id] = stop_event

    bot.send_message(chat_id, f"Szukam: {title} ({price_from}-{price_to} PLN) 🔍")
    threading.Thread(target=watch_items, args=(chat_id, url, stop_event), daemon=True).start()


def watch_items(chat_id, url, stop_event):
    previous_data = []
    while not stop_event.is_set():
        try:
            current_data = get_page_data(url)
        except Exception as e:
            bot.send_message(chat_id, f"Błąd parsingu: {e}")
            time.sleep(30)
            continue

        for item in current_data:
            if stop_event.is_set():
                return
            if item not in previous_data:
                previous_data.append(item)
                try:
                    bot.send_message(chat_id,
                                     f"Tytuł: {item['title']}\n"
                                     f"Cena: {item['price']}\n"
                                     f"{item['url']}")
                except Exception:
                    return

        # Проверяем каждые 30 секунд
        stop_event.wait(30)

    bot.send_message(chat_id, "Wyszukiwanie zakończone.")


@bot.message_handler(commands=['stop'])
def stop_search(message):
    chat_id = message.chat.id
    if chat_id in stop_events:
        stop_events[chat_id].set()
        del stop_events[chat_id]
        bot.send_message(chat_id, "Zatrzymano wyszukiwanie ✋")
    else:
        bot.send_message(chat_id, "Brak aktywnego wyszukiwania.")


@bot.message_handler(func=lambda message: message.text.lower() == "profil")
@bot.message_handler(commands=['profile'])
def profile(message):
    user = session.query(User).filter_by(name=message.from_user.username).first()
    if user:
        bot.send_message(message.chat.id, 'Jesteś już zarejestrowany')
        return
    user_name = message.from_user.username
    if not user_name:
        bot.send_message(message.chat.id, 'Musisz mieć username w Telegramie')
        return
    current_unix_time = int(time.time())

    user = User(name=user_name, date=current_unix_time)
    session.add(user)
    session.commit()

    bot.send_message(message.chat.id, 'Użytkownik zarejestrowany ✅')


if __name__ == '__main__':
    print("Bot started...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
