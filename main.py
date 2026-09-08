import telebot
import requests
import urllib.parse
import g4f

# Ваш токен от Telegram-бота apteka
TELEGRAM_TOKEN = '8836578040:AAGYmbBxH2Ohp16v2FYL-U7hm-p0Zx6h3lE'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я твой продвинутый ИИ-бот.\n\n"
        "💬 **Общение:** Просто напиши мне любой вопрос, и я отвечу.\n"
        "🎨 **Картинки:** Напиши `/img` и описание на английском или русском "
        "(например: `/img котик в шляпе`), чтобы я сгенерировал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    prompt = message.text.replace('/img', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img красивый пейзаж`")
        return
        
    bot.reply_to(message, f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 10-20 секунд.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        # Безопасное кодирование русского текста для URL ссылки
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# ОБЫЧНЫЙ ТЕКСТОВЫЙ ЧАТ С ИИ
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Используем автоматический подбор рабочих провайдеров, не требующих авторизации и браузера
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": user_text}],
        )
        
        ai_response = response if response else "Извините, не удалось получить осмысленный ответ."
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"Извините, сервер ИИ сейчас перегружен. Попробуйте еще раз. Ошибка: {e}")

if __name__ == '__main__':
    print("ИИ-Бот с генерацией картинок успешно запущен!")
    bot.infinity_polling()
