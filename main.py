import telebot
import requests
import urllib.parse
import g4f

# Ваш токен от Telegram-бота apteka
TELEGRAM_TOKEN = '8836578040:AAGYmbBxH2Ohp16v2FYL-U7hm-p0Zx6h3lE'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Бот автоматически узнает свое имя в Telegram при запуске
BOT_USERNAME = bot.get_me().username

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я твой продвинутый ИИ-бот.\n\n"
        "💬 **В группе:** Напишите мое имя @" + BOT_USERNAME + " и ваш вопрос, чтобы я ответил.\n"
        "🎨 **Картинки:** Напишите команду `/img` и описание (например: `/img котик`), чтобы я нарисовал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    # Очищаем запрос от команды и имени бота, если его тегнули
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img красивый пейзаж`")
        return
        
    bot.reply_to(message, f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 10-20 секунд.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# УМНАЯ ОБРАБОТКА ТЕКСТА ДЛЯ ГРУПП (Ответ только по зову)
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    
    # Проверяем условия
    is_group = message.chat.type in ['group', 'supergroup']
    is_mentioned = f"@{BOT_USERNAME}" in user_text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    
    # ЕСЛИ ЭТО ГРУППА: бот отвечает ТОЛЬКО если его тегнули или ответили на его сообщение
    if is_group:
        if not (is_mentioned or is_reply_to_bot):
            return  # Бот просто игнорирует чужой разговор

    # Очищаем текст от технического имени бота, чтобы нейросеть не путалась
    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()
    
    if not clean_text:
        bot.reply_to(message, "Я тут! Задайте мне любой вопрос.")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": clean_text}],
        )
        ai_response = response if response else "Извините, не удалось получить осмысленный ответ."
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"Извините, сервер ИИ сейчас перегружен. Попробуйте еще раз. Ошибка: {e}")

if __name__ == '__main__':
    print("ИИ-Бот с ответами по упоминанию успешно запущен!")
    bot.infinity_polling()
