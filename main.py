import telebot
import requests

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAGYmbBxH2Ohp16v2FYL-U7hm-p0Zx6h3lE'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
BOT_USERNAME = bot.get_me().username

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я твой новый, стабильный ИИ-бот.\n\n"
        "💬 **Общение:** Пиши мне любые вопросы, и я отвечу.\n"
        "🎨 **Картинки:** Напиши `/img` и описание, чтобы я нарисовал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки. Пример: `/img котик`")
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

# ОБЩЕНИЕ С ИИ ЧЕРЕЗ ЧИСТЫЙ ЗАПРОС К GPT-4O-MINI
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    
    is_group = message.chat.type in ['group', 'supergroup']
    is_mentioned = f"@{BOT_USERNAME}" in user_text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    
    if is_group and not (is_mentioned or is_reply_to_bot):
        return

    clean_text = user_text.replace(f"@{BOT_USERNAME}", "").strip()
    if not clean_text:
        bot.reply_to(message, "Слушаю вас!")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # 1. Получаем технический токен от DuckDuckGo
        headers = {"x-client-variant": "chat"}
        res = requests.get("https://duckduckgo.com", headers=headers)
        v_token = res.headers.get("x-vqd-accept")

        # 2. Отправляем чистый запрос пользователя без блокирующих инструкций
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": clean_text}]
        }
        headers["x-vqd-4"] = v_token
        
        response = requests.post("https://duckduckgo.com", headers=headers, json=payload)
        
        # Декодируем потоковый ответ сервера
        lines = response.text.split("\n")
        ai_response = ""
        for line in lines:
            if line.startswith("data:"):
                import json
                try:
                    data_json = json.loads(line[5:])
                    if "message" in data_json:
                        ai_response += data_json["message"]
                except:
                    pass
        
        if not ai_response:
            ai_response = "Извините, не удалось получить ответ. Попробуйте перефразировать вопрос."
            
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения с ИИ. Детали: {e}")

if __name__ == '__main__':
    print("Стабильная версия бота успешно запущена!")
    bot.infinity_polling()
