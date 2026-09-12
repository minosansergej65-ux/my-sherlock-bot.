import telebot
import requests
import os
import base64
import io
from flask import Flask, request

# ==========================================
# НАСТРОЙКИ (КЛЮЧИ ВСТАВЛЕНЫ ЖЕСТКО ДЛЯ НАДЕЖНОСТИ)
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
        "💬 Просто напиши мне вопрос — я отвечу.\n\n"
        "🎨 Генерация изображений:\n"
        "/img кот в космосе\n\n"
        "✨ Для генерации используются модели ProxyAPI."
    )
    bot.reply_to(message, welcome_text)


# ==========================================
# ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ ЧЕРЕЗ PROXYAPI (ВАШ ВАРИАНТ)
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
            "Пример:\n"
            "/img реалистичный кот на крыше Парижа ночью"
        )
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')

    status_message = bot.reply_to(
        message,
        "🎨 Генерирую изображение...\n"
        "⏳ Подожди немного..."
    )

    try:
        url = "https://api.proxyapi.ru/v1/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # Используется модель и параметры из вашего запроса
        payload = {
            "model": "openai/gpt-image-2",
            "prompt": prompt,
            "quality": "high",
            "size": "1024x1024",
            "output_format": "jpeg",
            "output_compression": 90,
            "n": 1
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=300
        )

        print("PROXYAPI STATUS:", response.status_code)
        print("PROXYAPI RESPONSE:", response.text[:2000])

        if response.status_code != 200:
            bot.edit_message_text(
                f"❌ ProxyAPI вернул ошибку: {response.status_code}\n\n"
                f"{response.text[:1000]}",
                message.chat.id,
                status_message.message_id
            )
            return

        result = response.json()

        if "data" not in result:
            raise Exception(
                f"В ответе ProxyAPI нет поля data: {result}"
            )

        if not result["data"]:
            raise Exception(
                f"ProxyAPI вернул пустой data: {result}"
            )

        if "b64_json" not in result["data"][0]:
            raise Exception(
                f"В ответе нет b64_json: {result}"
            )

        image_base64 = result["data"][0]["b64_json"]

        image_bytes = base64.b64decode(image_base64)

        image_file = io.BytesIO(image_bytes)
        image_file.name = "generated.jpg"

        try:
            bot.delete_message(
                message.chat.id,
                status_message.message_id
            )
        except Exception:
            pass

        bot.send_photo(
            message.chat.id,
            image_file,
            caption=f"✨ Готово!\n\n📝 {prompt}"
        )

    except Exception as e:
        print("================================")
        print("IMAGE GENERATION ERROR:")
        print(repr(e))
        print("================================")

        try:
            bot.edit_message_text(
                "❌ Ошибка при генерации.\n\n"
                f"Причина: {str(e)[:1000]}",
                message.chat.id,
                status_message.message_id
            )
        except Exception:
            bot.reply_to(
                message,
                f"❌ Ошибка: {str(e)[:1000]}"
            )


# ==========================================
# ТЕКСТОВЫЙ ИИ (ОФИЦИАЛЬНЫЙ PROXYAPI С ОБНОВЛЕННОЙ ССЫЛКОЙ)
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

    # Быстрое фирменное приветствие
    if clean_text.lower() in ["привет", "привееет", "приветик", "hi", "hello"]:
        bot.reply_to(message, "Привет, я AptekaAI! 🤖 Чем могу помочь?")
        return

    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Ссылка с префиксом /v1 для единого формата шлюза
        url = "https://proxyapi.ru"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # Модель указана с правильным вендором по новым правилам
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
            bot.reply_to(message, f"❌ Ошибка шлюза ИИ (код {response.status_code}). Проверьте баланс на сайте proxyapi.ru.")

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
