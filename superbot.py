import telebot
from telebot import types
import requests
from setup import Api_key

API_TOKEN = Api_key
bot = telebot.TeleBot(API_TOKEN)

API_URL = 'https://api.exchangerate-api.com/v4/latest/UAH'

user_data = {}


def get_currency_rate(base_currency, target_currency):
    response = requests.get(f'https://api.exchangerate-api.com/v4/latest/{base_currency}')
    data = response.json()
    return data['rates'].get(target_currency, "Немає даних")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Курс валют", callback_data='rate_menu'))
    keyboard.add(types.InlineKeyboardButton("Конвертувати валюту", callback_data='convert_menu'))
    bot.send_message(message.chat.id, f"Привіт, {user_first_name}!\nЩо ви хочете зробити?", reply_markup=keyboard)


def send_currency_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Курс Доллара", callback_data='USD_rate'))
    keyboard.add(types.InlineKeyboardButton("Курс Євро", callback_data='EUR_rate'))
    bot.send_message(chat_id, "Виберіть валюту (ціна в UAH):", reply_markup=keyboard)


def send_base_currency_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("USD", callback_data='USD_base'))
    keyboard.add(types.InlineKeyboardButton("EUR", callback_data='EUR_base'))
    keyboard.add(types.InlineKeyboardButton("UAH", callback_data='UAH_base'))
    bot.send_message(chat_id, "Виберіть базову валюту:", reply_markup=keyboard)


def send_target_currency_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("USD", callback_data='USD_target'))
    keyboard.add(types.InlineKeyboardButton("EUR", callback_data='EUR_target'))
    keyboard.add(types.InlineKeyboardButton("UAH", callback_data='UAH_target'))
    bot.send_message(chat_id, "Виберіть цільову валюту:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'rate_menu':
        send_currency_keyboard(call.message.chat.id)
    elif call.data == 'convert_menu':
        bot.send_message(call.message.chat.id, "Виберіть валюту, з якої ви хочете конвертувати:")
        send_base_currency_keyboard(call.message.chat.id)
    elif '_rate' in call.data:
        currency = call.data.replace('_rate', '')
        rate = get_currency_rate('UAH', currency)
        if rate != "Немає даних":
            rate = 1 / rate  # Перетворення вартість 1 валюти в UAH
            bot.send_message(call.message.chat.id, f"Курс 1 {currency} = {rate:.2f} UAH")
        else:
            bot.send_message(call.message.chat.id, f"Курс для {currency} не знайдено.")
    elif '_base' in call.data:
        user_data[call.message.chat.id] = {'base': call.data.replace('_base', '')}
        bot.send_message(call.message.chat.id, "Виберіть цільову валюту:")
        send_target_currency_keyboard(call.message.chat.id)
    elif '_target' in call.data:
        user_data[call.message.chat.id]['target'] = call.data.replace('_target', '')
        bot.send_message(call.message.chat.id, "Введіть суму для конвертації:")
        bot.register_next_step_handler(call.message, get_amount)
    bot.answer_callback_query(call.id)


def get_amount(message):
    try:
        amount = float(message.text)
        base_currency = user_data[message.chat.id]['base']
        target_currency = user_data[message.chat.id]['target']
        rate = get_currency_rate(base_currency, target_currency)
        if rate != "Немає даних":
            converted_amount = amount * rate
            converted_amount_rounded = round(converted_amount)
            bot.send_message(message.chat.id, f"{amount} {base_currency} = {converted_amount_rounded} {target_currency}")
        else:
            bot.send_message(message.chat.id, "Не вдалося отримати курс валюти.")
    except ValueError:
        bot.send_message(message.chat.id, "Будь ласка, введіть правильне число.")


bot.polling()
