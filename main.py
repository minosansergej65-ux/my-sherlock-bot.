import telebot
import requests
import threading
import time

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAGYmbBxH2Ohp16v2FYL-U7hm-p0Zx6h3lE'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
BOT_USERNAME = bot.get_me().username

# ФУНКЦИЯ АВТО-ПИНГА (НЕ ДАЕТ СЕРВЕРУ УСНУТЬ)
def keep_alive():
    while True:
        try:
            # Бот каждые 5 минут пингует сам себя или открытый сервер, чтобы Render думал, что сайт активен
            requests.get("https://pollinations.ai")
            print("Пинг сервера выполнен успешно!")
        except:
            pass
        time.sleep(300) # Повторять каждые 5 минут

# Запуск пинга в отдельном потоке
threading.Thread(target=keep_alive, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я твой ВЕЧНЫЙ ИИ-бот БЕЗ ОГРАНИЧЕНИЙ.\n\n"
        "💬 **Общение:** Пиши мне любые вопросы, я отвечу без блокировок.\n"
        "🎨 **Картинки:** Напиши `/img` и описание, чтобы я нарисовал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Напишите описание картинки. Пример: `/img котик`")
        return
    bot.reply_to(message, f"🎨 Рисую: *\"{prompt}\"*...", parse_mode="Markdown")
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово: {prompt}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка картинок: {e}")

# СТАБИЛЬНЫЙ ТЕКСТОВЫЙ ЧАТ БЕЗ ОГРАНИЧЕНИЙ
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    is_group = message.chat.type in ['group', 'supergroup']
    if is_group and not (f"@{BOT_USERNAME}" in user_text or (message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id)):
        return
    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()
    if not clean_text:
        bot.reply_to(message, "Слушаю вас!")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        url = "https://aryahcr.cc"
        payload = {"messages": [{"role": "user", "content": clean_text}], "stream": False}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            ai_response = response.json().get('gpt', 'Сервер пуст.')
        else:
            ai_response = "Попробуйте еще раз чуть позже."
        bot.reply_to(message, ai_response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка ИИ: {e}")

if __name__ == '__main__':
    bot.infinity_polling()
