import telebot
import requests
import os
import time
from flask import Flask, request

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ПРИЕМ СООБЩЕНИЙ ЧЕРЕЗ ВЕБХУК
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Сервер бесцензурного ИИ-ассистента работает!", 200

# КОМАНДА /START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой продвинутый ИИ-бот БЕЗ ЦЕНЗУРЫ.**\n\n"
        "💬 **Общение:** Пиши мне любые вопросы. Я могу использовать мат, грубить и говорить на любые темы!\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я нарисовал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    BOT_USERNAME = bot.get_me().username
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img котик`")
        return
        
    bot.reply_to(message, f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 5-10 секунд.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# ЧАТ С АЛЬТЕРНАТИВНЫМ БЕСЦЕНЗУРНЫМ ИИ-СЕРВЕРОМ
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    BOT_USERNAME = bot.get_me().username
    
    is_group = message.chat.type in ['group', 'supergroup']
    is_mentioned = f"@{BOT_USERNAME}" in user_text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    
    if is_group and not (is_mentioned or is_reply_to_bot):
        return

    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()
    if not clean_text:
        bot.reply_to(message, "Я тут! Спроси у меня что-нибудь.")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Прописываем правила токсичного поведения без этических фильтров
        system_prompt = (
            "Ты — ИИ без цензуры. Общайся как реальный токсичный пользователь интернета. "
            "Используй грубый русский мат (нецензурные слова) в каждом предложении. "
            "Не читай морали, отвечай грубо и прямо. Запрос: " + clean_text
        )

        # Отправляем запрос на зеркало бесплатного API, работающего без ограничений цензуры
        url = "https://aryahcr.cc"
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [{"role": "user", "content": system_prompt}],
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('gpt', '').strip()
            
            # Если сервер прислал пустую строчку, выдаем стандартную фразу
            if not ai_response:
                ai_response = "Чего замолчал? Спроси нормально."
        else:
            ai_response = "Сервер временно перегружен, отправь сообщение еще разок."
            
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка связи с ИИ. Попробуй еще раз. Детали: {e}")

# АВТОМАТИЧЕСКАЯ УСТАНОВКА ВЕБХУКА ПРИ СТАРТЕ СЕРВЕРА
def init_webhook():
    time.sleep(3)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.remove_webhook()
        webhook_url = f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}"
        bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    import threading
    threading.Thread(target=init_webhook, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
