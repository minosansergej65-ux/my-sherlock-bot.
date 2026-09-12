import telebot
import requests
import os
from flask import Flask, request

# ==========================================
# НАСТРОЙКИ (КЛЮЧИ НАДЕЖНО ВСТАВЛЕНЫ)
# ==========================================

TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'
API_KEY = 'sk-fqLxyf8Vypai3VQoXBDwpYp6YLpVETiB'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)


# ==========================================
# WEBHOOK
# ==========================================

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@app.route("/")
def index():
    return "Официальный ИИ-сервер запущен!", 200


# ==========================================
# /START
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 Привет! Я AptekaAI.\n\n"
        "💬 Просто напиши мне вопрос — я отвечу (это стоит копейки!).\n\n"
        "🎨 **Бесплатные картинки:**\n"
        "/img кот в космосе\n\n"
        "✨ Картинки теперь на 100% бесплатны и не тратят твой баланс!"
    )
    bot.reply_to(message, welcome_text)


# ==========================================
# 🎨 100% БЕСПЛАТНАЯ ГЕНЕРАЦИЯ КАРТИНОК (СПАСАЕМ БАЛАНС!)
# ==========================================

@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    BOT_USERNAME = bot.get_me().username
    prompt = message.text.replace('/img', '', 1)

    if BOT_USERNAME:
        prompt = prompt.replace(f'@{BOT_USERNAME}', '')

    prompt = prompt.strip()

    if not prompt:
        bot.reply_to(
            message,
            "❌ Напиши описание картинки.\n\n"
            "Например:\n"
            "/img красивый закат в горах"
        )
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')
    status_message = bot.reply_to(
        message,
        "🎨 Рисую изображение на бесплатном сервере...\n⏳ Это займет около 5-10 секунд."
    )

    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Подключаем самый мощный БЕСПЛАТНЫЙ движок Flux
        image_url = f"https://pollinations.ai{encoded_prompt}&width=1024&height=1024&seed=42&nofeed=true"
        
        img_data = requests.get(image_url).content
        
        try:
            bot.delete_message(message.chat.id, status_message.message_id)
        except:
            pass

        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово бесплатно!\n\n📝 {prompt}")

    except Exception as e:
        print("IMAGE GENERATION ERROR:", e)
        bot.edit_message_text(
            "❌ Произошла ошибка при генерации изображения.\nПопробуйте ещё раз.",
            message.chat.id,
            status_message.message_id
        )


# ==========================================
# ТЕКСТОВЫЙ ИИ (ОЧЕНЬ ДЕШЕВЫЙ CHATGPT)
# ==========================================

@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    BOT_USERNAME = bot.get_me().username
    is_group = message.chat.type in ['group', 'supergroup']

    is_mentioned = (
        BOT_USERNAME and
        f"@{BOT_USERNAME}" in user_text
    )

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user.id == bot.get_me().id
    )

    if is_group and not (is_mentioned or is_reply_to_bot):
        return

    clean_text = user_text
    if BOT_USERNAME:
        clean_text = clean_text.replace(f"@{BOT_USERNAME}", "")
    clean_text = clean_text.strip()

    if not clean_text:
        bot.reply_to(message, "Я здесь! Чем могу помочь?")
        return

    # Быстрое фирменное приветствие (тоже бесплатно)
    if clean_text.lower() in ["привет", "привееет", "приветик", "hi", "hello"]:
        bot.reply_to(message, "Привет, я AptekaAI! 🤖 Чем могу помочь?")
        return

    bot.send_chat_action(message.chat.id, 'typing')

    try:
        url = "https://proxyapi.ru"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # Самая экономичная и умная модель gpt-4o-mini
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — полезный, умный и вежливый ИИ-ассистент AptekaAI. Отвечай понятно, грамотно и дружелюбно на русском языке."
                },
                {
                    "role": "user",
                    "content": clean_text
                }
            ],
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"].strip()
            bot.reply_to(message, ai_response)
        else:
            print("TEXT API ERROR:", response.status_code, response.text)
            bot.reply_to(message, f"❌ Ошибка шлюза ИИ. Проверьте баланс на сайте proxyapi.ru.")

    except Exception as e:
        print("TEXT ERROR:", e)
        bot.reply_to(message, "❌ Ошибка соединения с ИИ.")


# ==========================================
# ЗАПУСК ВЕБХУКА
# ==========================================

if __name__ == '__main__':
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
