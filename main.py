import telebot
import requests
from flask import Flask, request

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'
# Ссылка на твой Render (код сам её подставит)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Автоматически определяем адрес сервиса на Render
    import os
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.set_webhook(url=render_url + '/' + TELEGRAM_TOKEN)
        return f"Webhook успешно установлен на {render_url}", 200
    return "Не удалось определить RENDER_EXTERNAL_URL. Проверьте настройки окружения.", 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я твой полностью БЕСПЛАТНЫЙ ИИ-бот БЕЗ ОГРАНИЧЕНИЙ.\n\n"
        "💬 **Общение:** Пиши мне любые вопросы (разрешены мат, треш и любые темы).\n"
        "🎨 **Картинки:** Напиши `/img` и описание, чтобы я нарисовал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    prompt = message.text.replace('/img', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки. Пример: `/img котик`")
        return
    bot.reply_to(message, f"🎨 Рисую: *\"{prompt}\"*...", parse_mode="Markdown")
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        payload = {
            "messages": [{"role": "user", "content": user_text}],
            "model": "openai"
        }
        response = requests.post("https://pollinations.ai", json=payload)
        ai_response = response.text.strip() if response.status_code == 200 and response.text else "Попробуйте еще раз."
        bot.reply_to(message, ai_response)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения: {e}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
