import telebot
import requests
import os
from flask import Flask, request

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'
# ТВОЙ ОФИЦИАЛЬНЫЙ КЛЮЧ OPENAI
OPENAI_API_KEY = 'sk-DM6qOt35yk3ZzFHGgqb8CqmtDZGJU8K8'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Прием сообщений через вебхук (обязательно для Render)
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Официальный ИИ-сервер работает!", 200

# КОМАНДА /START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой официальный ИИ-ассистент на базе ChatGPT.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание, чтобы я создал изображение!"
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

# ЧИСТЫЙ ЗАПРОС К ОФИЦИАЛЬНОМУ CHATGPT
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
        bot.reply_to(message, "Я здесь! Чем я могу помочь?")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        url = "https://openai.com"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        # Кристально чистый промпт обычного ассистента OpenAI
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай подробно и грамотно на русском языке."},
                {"role": "user", "content": clean_text}
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices']['message']['content'].strip()
        else:
            ai_response = f"❌ Ошибка OpenAI (Код {response.status_code}). Пожалуйста, убедитесь, что на аккаунте ://openai.com пополнен баланс API (Credit balance)."
            
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения. Детали: {e}")

# Автоматический запуск вебхука
if __name__ == '__main__':
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
