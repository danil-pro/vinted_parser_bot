import telebot
from config import TOKEN, URL
from parser import get_page_data
import time
from db import session, User
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
from pyVinted import Vinted

vinted = Vinted()

bot = telebot.TeleBot(TOKEN)

scheduler = BackgroundScheduler()
scheduler.start()


@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Profil")  # Профиль
    item2 = types.KeyboardButton("Produkty")  # Товары

    markup.add(item1, item2)

    # Приветствие на польском
    welcome_message = "Witaj! Wybierz opcję:"

    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.lower() == "produkty")
def closet_title(message):
    bot.send_message(message.chat.id, 'Napisz nazwę przedmiotu')
    get_closet(message, stop=True)
    bot.register_next_step_handler(message, closet_price_to)


def closet_price_to(message):
    title = message.text
    bot.send_message(message.chat.id, 'Napisz maksymalną cenę')  # Напишите максимальную цену

    # Добавляем title в контекст для передачи в следующий обработчик
    bot.register_next_step_handler(message, closet_price_from, title)


def closet_price_from(message, title):
    price_to = message.text
    bot.send_message(message.chat.id, 'Napisz minimalną cenę')  # Напишите минимальную цену

    # Добавляем title в контекст для передачи в следующий обработчик
    bot.register_next_step_handler(message, get_closet, title, price_to)


def get_closet(message, title=None, price_to=None, stop=False):
    user = session.query(User).filter_by(name=message.from_user.username).first()
    if not user:
        bot.send_message(message.chat.id, 'Zaloguj się na /profil')  # Зайди на /profile
        return
    if stop:
        return

    price_from = message.text

    url = (URL + "%20".join(title.split()) +
           '&order=newest_first' +
           f'&price_to={price_to}' +
           f'&price_from={price_from}' +
           '&currency=PLN')

    print(url)
    bot.send_message(message.chat.id, "Czekaj 💫")  # Жди 💫
    previous_data = []

    while True:
        current_data = get_page_data(url)

        for item in current_data:
            if item not in previous_data:
                previous_data.append(item)
                bot.send_message(message.chat.id,
                                 f"Tytuł: {item['title']}\n"
                                 f"Cena: {item['price']}\n"
                                 f"{item['url']}",
                                 parse_mode='html')
                bot.send_message(message.chat.id, "Czekaj 💫")  # Жди 💫
                time.sleep(10)

        time.sleep(5)


@bot.message_handler(func=lambda message: message.text.lower() == "profil")
@bot.message_handler(commands=['profile'])
def profile(message):
    user = session.query(User).filter_by(name=message.from_user.username).first()
    if user:
        bot.send_message(message.chat.id, 'Jesteś już zarejestrowany')  # Вы уже были зарегистрированы
        return
    user_name = message.from_user.username
    current_unix_time = int(time.time())

    user = User(name=user_name, date=current_unix_time)
    session.add(user)
    session.commit()

    bot.send_message(message.chat.id, 'Użytkownik zarejestrowany')  # Пользователь зарегистрирован


bot.infinity_polling(timeout=10, long_polling_timeout=5)
