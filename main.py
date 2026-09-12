import telebot
import requests
import os
from flask import Flask, request

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'
# ТВОЙ АКТИВНЫЙ API КЛЮЧ PROXYAPI
API_KEY = 'sk-fqLxyf8Vypai3VQoXBDwpYp6YLpVETiB'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Прием сообщений через вебхук
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Официальный ИИ-сервер запущен!", 200

# КОМАНДА /START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой новый, официальный ИИ-ассистент на базе ChatGPT.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я создал изображение!"
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
        image_url = f"https://pollinations.ai{encoded_prompt}&nofeed=true"
        
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Попробуйте изменить запрос.")

# ЧАТ С ОФИЦИАЛЬНЫМ CHATGPT (ОБНОВЛЕННЫЙ ИДЕНТИФИКАТОР МОДЕЛИ)
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
        bot.reply_to(message, "Я здесь! Чем я могу вам помочь?")
        return

    # МГНОВЕННОЕ ФИРМЕННОЕ ПРИВЕТСТВИЕ
    if clean_text.lower() in ["привет", "привееет", "приветик", "hi", "hello"]:
        bot.reply_to(message, "Привет, я AptekaAi! 🤖 Чем могу помочь?")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Официальный адрес Единого API ProxyAPI
        url = "https://api.proxyapi.ru/v1/chat/completions"
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        # СТРОГО УКАЗЫВАЕМ ПОЛНОЕ ИМЯ МОДЕЛИ С ВЕНДОРОМ ПО НОВЫМ ПРАВИЛАМ
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, грамотно и дружелюбно на русском языке."},
                {"role": "user", "content": clean_text}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
        else:
            ai_response = f"❌ Ошибка шлюза ИИ (Код {response.status_code}). Пожалуйста, проверьте баланс на сайте proxyapi.ru."
            
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения с ИИ. Детали: {e}")

# Автоматический запуск вебхука
if __name__ == '__main__':
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
