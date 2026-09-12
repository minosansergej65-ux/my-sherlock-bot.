import telebot
import requests
import os
import json
from flask import Flask, request

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Официальный ИИ-сервер работает стабильно!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой новый, стабильный ИИ-помощник.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я создал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ ЧЕРЕЗ БЕЗОПАСНЫЙ POST
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
        # Отправляем данные защищенным способом в теле запроса (POST) вместо адресной строки
        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "model": "flux",
            "n": 1
        }
        response = requests.post("https://pollinations.ai", json={"messages": [{"role": "user", "content": f"Сгенерируй картинку: {prompt}"}], "model": "image"}, timeout=20)
        
        # Если POST-метод вернул прямую ссылку
        if response.status_code == 200 and "http" in response.text:
            image_url = response.text.strip()
            img_data = requests.get(image_url).content
            bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        else:
            # Запасной легкий вариант без кодирования
            image_url = f"https://pollinations.ai{prompt}&nofeed=true"
            img_data = requests.get(image_url).content
            bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Попробуйте на английском или измените запрос.")

# ОБЩЕНИЕ ЧЕРЕЗ СВЕРХСТАБИЛЬНЫЙ СЕРВЕР DUCKDUCKGO (БЕЗ ОШИБОК ССЫЛКИ)
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
        system_prompt = "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, грамотно и дружелюбно на русском языке."

        # 1. Получаем технический токен от DuckDuckGo
        headers = {"x-client-variant": "chat", "User-Agent": "Mozilla/5.0"}
        res = requests.get("https://duckduckgo.com", headers=headers, timeout=10)
        v_token = res.headers.get("x-vqd-accept")

        # 2. Отправляем запрос к мощной свободной модели gpt-4o-mini
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_text}
            ]
        }
        headers["x-vqd-4"] = v_token
        headers["Content-Type"] = "application/json"
        
        response = requests.post("https://duckduckgo.com", headers=headers, json=payload, timeout=15)
        
        # Декодируем потоковый ответ сервера DuckDuckGo
        lines = response.text.split("\n")
        ai_response = ""
        for line in lines:
            if line.startswith("data:"):
                try:
                    data_json = json.loads(line[5:])
                    if "message" in data_json:
                        ai_response += data_json["message"]
                except:
                    pass
        
        if not ai_response:
            ai_response = "Извините, не удалось получить осмысленный ответ. Попробуйте еще раз."
            
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, "Извините, произошел сбой сети. Пожалуйста, повторите вопрос чуть позже.")

if __name__ == '__main__':
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
