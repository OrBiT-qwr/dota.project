import config
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3 

bot = telebot.TeleBot(config.API_TOKEN)

# 1. Функция отправки карточки одного героя
def send_info(bot, message, row):
    # row[0] - name, row[1] - winrate, row[2] - role
    info = f"""
📍 Герой: {row[0]}
📈 Винрейт: {row[1]}%
⚔️ Роль: {row[2]}
"""
    bot.send_message(message.chat.id, info)

def main_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/random'))
    # Кнопки должны в точности совпадать с названиями в вашей базе данных
    markup.add(KeyboardButton('Керри'), KeyboardButton('Мидер'))
    markup.add(KeyboardButton('Оффлейнер'), KeyboardButton('Саппорт'))
    return markup

# 2. Старт
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
        "Привет! Я бот по героям Dota 2 (2025).\n"
        "• Нажми на кнопку роли, чтобы увидеть список (сортировка по винрейту).\n"
        "• Напиши имя героя (или /имя), чтобы узнать детали.\n"
        "• Нажми /random для случайного героя.", 
        reply_markup=main_markup())

# 3. Случайный герой
@bot.message_handler(commands=['random'])
def random_hero(message):
    try:
        con = sqlite3.connect("dota.db")
        cur = con.cursor()
        cur.execute("SELECT name, winrate, role FROM data ORDER BY RANDOM() LIMIT 1")
        res = cur.fetchone()
        if res:
            send_info(bot, message, res)
        con.close()
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка базы данных.")

# 4. Поиск по РОЛИ (Сортировка винрейта снизу вверх)
@bot.message_handler(func=lambda message: message.text.lower() in ['керри', 'мидер', 'оффлейнер', 'саппорт'])
def get_heroes_by_role(message):
    role_input = message.text.lower().strip()
    con = sqlite3.connect("dota.db")
    cur = con.cursor()
    
    # Используем LIKE, так как у героя может быть несколько ролей через запятую
    # CAST нужен, если винрейт в базе хранится как текст
    query = "SELECT name, winrate FROM data WHERE LOWER(role) LIKE ? ORDER BY CAST(winrate AS FLOAT) ASC"
    cur.execute(query, (f'%{role_input}%',))
    rows = cur.fetchall()
    
    if rows:
        bot.send_message(message.chat.id, f"📊 Роль: {message.text.upper()}\n(От низкого винрейта к высокому)")
        
        response = ""
        for row in rows:
            response += f"📈 {row[1]}% — {row[0]}\n"
            if len(response) > 3000:
                bot.send_message(message.chat.id, response)
                response = ""
        if response:
            bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, f"В базе не найдено героев с ролью '{message.text}'")
    con.close()

# 5. Команды со слешем (напр. /pudge)
@bot.message_handler(func=lambda message: message.text.startswith('/') and message.text not in ['/start', '/random'])
def get_hero_by_command(message):
    hero_name = message.text[1:].lower()
    con = sqlite3.connect("dota.db")
    cur = con.cursor()
    cur.execute("SELECT name, winrate, role FROM data WHERE LOWER(name) = ?", (hero_name,))
    row = cur.fetchone()
    if row:
        send_info(bot, message, row)
    else:
        bot.send_message(message.chat.id, "Герой не найден.")
    con.close()

# 6. Поиск просто по названию
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    con = sqlite3.connect("dota.db")
    cur = con.cursor()
    cur.execute("SELECT name, winrate, role FROM data WHERE LOWER(name) = ?", (message.text.lower(),))
    row = cur.fetchone()
    
    if row:
        bot.send_message(message.chat.id, "Герой найден:")
        send_info(bot, message, row)
    else:
        bot.send_message(message.chat.id, "Я не знаю такого героя или роли. Попробуй кнопки ниже 👇")
    con.close()

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    bot.infinity_polling()
