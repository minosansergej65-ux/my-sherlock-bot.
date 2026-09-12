import telebot
import requests
import os
import base64
import io
import sqlite3
from flask import Flask, request
from datetime import date


# =========================================================
# НАСТРОЙКИ
# =========================================================

TELEGRAM_TOKEN = "8836578040:AAF2Psd-Non7Avua_8k9cOx4aLtk1hz-Ku3do"
API_KEY = "sk-fqLxyf8Vypai3VQoXBDwp-Yp6YLpVETiB"

# Твой Telegram ID
OWNER_ID = 8948282169

# Цены в Telegram Stars
UNLIMITED_PRICE_STARS = 100
IMAGE_PRICE_STARS = 10

# Бесплатный лимит обычного пользователя
DAILY_FREE_MESSAGES = 100


if not TELEGRAM_TOKEN:
    raise ValueError("Не найден TELEGRAM_TOKEN")

if not API_KEY:
    raise ValueError("Не найден PROXYAPI_KEY")


# =========================================================
# БАЗА ДАННЫХ (SQLite)
# =========================================================

DB_NAME = "apteka_users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            date TEXT,
            messages INTEGER DEFAULT 0,
            unlimited INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    today = str(date.today())
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT date, messages, unlimited FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, date, messages, unlimited) VALUES (?, ?, 0, 0)",
            (user_id, today)
        )
        conn.commit()
        conn.close()
        return {"date": today, "messages": 0, "unlimited": False}

    db_date, messages, unlimited = row

    # Новый день — сбрасываем счётчик
    if db_date != today:
        cursor.execute(
            "UPDATE users SET date = ?, messages = 0 WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()
        messages = 0
        db_date = today

    conn.close()
    return {
        "date": db_date,
        "messages": messages,
        "unlimited": bool(unlimited)
    }

def update_user_messages(user_id, messages):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET messages = ? WHERE user_id = ?",
        (messages, user_id)
    )
    conn.commit()
    conn.close()

def set_unlimited(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET unlimited = 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

init_db()


# =========================================================
# TELEGRAM
# =========================================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)


# Временное хранилище запросов на картинки (до оплаты)
pending_images = {}


def is_owner(user_id):
    return user_id == OWNER_ID


# =========================================================
# WEBHOOK
# =========================================================

@app.route("/" + TELEGRAM_TOKEN, methods=["POST"])
def getMessage():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@app.route("/")
def index():
    return "AptekaAI server is running!", 200


# =========================================================
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id

    if is_owner(user_id):
        welcome_text = (
            "👑 Привет, владелец AptekaAI!\n\n"
            "У тебя полный бесплатный доступ.\n\n"
            "💬 Текстовый ИИ — без ограничений\n"
            "🎨 Генерация изображений — бесплатно\n\n"
            "Команды:\n"
            "/img описание картинки\n"
            "/status — твой статус\n"
            "/buy — купить безлимит (для обычных пользователей)"
        )
    else:
        welcome_text = (
            "🤖 Привет! Я AptekaAI.\n\n"
            "💬 Первые 100 сообщений в сутки — бесплатно.\n\n"
            "🎨 Генерация изображений оплачивается отдельно.\n\n"
            "Пример:\n"
            "/img реалистичный кот на крыше Парижа ночью\n\n"
            "⭐ После бесплатного лимита можно купить безлимитный текстовый доступ.\n\n"
            "Команды:\n"
            "/status — сколько сообщений осталось\n"
            "/buy — купить безлимит\n"
            "/img описание"
        )

    bot.reply_to(message, welcome_text)


# =========================================================
# /STATUS
# =========================================================

@bot.message_handler(commands=["status"])
def status_command(message):
    user_id = message.from_user.id

    if is_owner(user_id):
        bot.reply_to(
            message,
            "👑 Ты владелец AptekaAI.\n"
            "У тебя полный безлимитный доступ."
        )
        return

    user = get_user(user_id)

    if user["unlimited"]:
        bot.reply_to(
            message,
            "⭐ У тебя активирован **безлимитный** текстовый доступ.\n"
            "Можешь писать сколько угодно."
        )
    else:
        left = max(0, DAILY_FREE_MESSAGES - user["messages"])
        bot.reply_to(
            message,
            f"📊 Твой статус:\n\n"
            f"💬 Использовано сегодня: {user['messages']} / {DAILY_FREE_MESSAGES}\n"
            f"✅ Осталось бесплатных сообщений: {left}\n\n"
            f"⭐ Купить безлимит: /buy"
        )


# =========================================================
# /BUY — КУПИТЬ БЕЗЛИМИТ
# =========================================================

@bot.message_handler(commands=["buy"])
def buy_unlimited(message):
    user_id = message.from_user.id

    if is_owner(user_id):
        bot.reply_to(
            message,
            "👑 Ты владелец AptekaAI.\n"
            "У тебя безлимитный доступ бесплатно."
        )
        return

    user = get_user(user_id)
    if user["unlimited"]:
        bot.reply_to(
            message,
            "⭐ У тебя уже активирован безлимитный доступ."
        )
        return

    bot.send_invoice(
        chat_id=message.chat.id,
        title="AptekaAI — безлимит",
        description="Безлимитные текстовые сообщения в AptekaAI без дневного ограничения.",
        invoice_payload=f"unlimited:{user_id}",
        provider_token="",
        currency="XTR",
        prices=[
            telebot.types.LabeledPrice(
                "Безлимитный текст",
                UNLIMITED_PRICE_STARS
            )
        ]
    )


# =========================================================
# /IMG — ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ
# =========================================================

@bot.message_handler(commands=["img"])
def handle_image_generation(message):
    user_id = message.from_user.id
    prompt = message.text.replace("/img", "", 1).strip()

    if not prompt:
        bot.reply_to(
            message,
            "❌ Напиши описание картинки.\n\n"
            "Например:\n"
            "/img реалистичный кот на крыше Парижа ночью"
        )
        return

    # Владелец — бесплатно
    if is_owner(user_id):
        bot.send_chat_action(message.chat.id, "upload_photo")
        status_message = bot.reply_to(
            message,
            "👑 Владелец — бесплатно.\n🎨 Генерирую изображение..."
        )
        generate_image(
            chat_id=message.chat.id,
            prompt=prompt,
            status_message=status_message
        )
        return

    # Обычный пользователь — сохраняем запрос и выставляем счёт
    pending_images[user_id] = {
        "prompt": prompt,
        "chat_id": message.chat.id
    }

    bot.send_invoice(
        chat_id=message.chat.id,
        title="AptekaAI — изображение",
        description="Одна генерация изображения через AptekaAI.",
        invoice_payload=f"image:{user_id}",
        provider_token="",
        currency="XTR",
        prices=[
            telebot.types.LabeledPrice(
                "Генерация изображения",
                IMAGE_PRICE_STARS
            )
        ]
    )


# =========================================================
# PRE-CHECKOUT
# =========================================================

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(query):
    try:
        payload = query.invoice_payload

        if not (payload.startswith("image:") or payload.startswith("unlimited:")):
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Неизвестный заказ."
            )
            return

        bot.answer_pre_checkout_query(query.id, ok=True)

    except Exception as e:
        print("PRE-CHECKOUT ERROR:", repr(e))
        try:
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Не удалось проверить заказ."
            )
        except Exception:
            pass


# =========================================================
# УСПЕШНАЯ ОПЛАТА
# =========================================================

@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    user_id = message.from_user.id
    payment = message.successful_payment
    payload = payment.invoice_payload

    print("================================")
    print("УСПЕШНАЯ ОПЛАТА")
    print("USER:", user_id)
    print("PAYLOAD:", payload)
    print("STARS:", payment.total_amount)
    print("CHARGE ID:", payment.telegram_payment_charge_id)
    print("================================")

    # Безлимитный текст
    if payload.startswith("unlimited:"):
        set_unlimited(user_id)
        bot.reply_to(
            message,
            "✅ Оплата получена!\n\n"
            "⭐ Безлимитный текстовый доступ активирован.\n"
            "Теперь ты можешь писать ИИ без дневного лимита."
        )
        return

    # Оплата изображения
    if payload.startswith("image:"):
        pending = pending_images.get(user_id)

        if not pending:
            bot.reply_to(
                message,
                "⚠️ Оплата получена, но запрос изображения не найден.\n\n"
                "Напиши /img ещё раз и обратись в поддержку: /paysupport"
            )
            return

        prompt = pending["prompt"]
        chat_id = pending["chat_id"]
        del pending_images[user_id]

        status_message = bot.reply_to(
            message,
            "💳 Оплата получена!\n\n🎨 Генерирую изображение..."
        )

        generate_image(
            chat_id=chat_id,
            prompt=prompt,
            status_message=status_message
        )
        return


# =========================================================
# ФУНКЦИЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЯ
# =========================================================

def generate_image(chat_id, prompt, status_message):
    try:
        bot.send_chat_action(chat_id, "upload_photo")

        url = "https://api.proxyapi.ru/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        payload = {
            "model": "openai/gpt-image-2",
            "prompt": prompt,
            "quality": "medium",
            "size": "1024x1024",
            "output_format": "jpeg",
            "output_compression": 90,
            "n": 1
        }

        response = requests.post(url, headers=headers, json=payload, timeout=180)

        print("PROXYAPI IMAGE STATUS:", response.status_code)
        print("PROXYAPI IMAGE RESPONSE:", response.text[:2000])

        if response.status_code != 200:
            try:
                bot.edit_message_text(
                    f"❌ Ошибка генерации.\n\nКод: {response.status_code}\n\n{response.text[:800]}",
                    chat_id,
                    status_message.message_id
                )
            except Exception:
                bot.reply_to(status_message, "❌ Ошибка генерации изображения.")
            return

        result = response.json()

        if "data" not in result or not result["data"]:
            raise Exception("ProxyAPI вернул пустой результат")

        if "b64_json" not in result["data"][0]:
            raise Exception("В ответе отсутствует b64_json")

        image_base64 = result["data"][0]["b64_json"]
        image_bytes = base64.b64decode(image_base64)
        image_file = io.BytesIO(image_bytes)
        image_file.name = "generated.jpg"

        try:
            bot.delete_message(chat_id, status_message.message_id)
        except Exception:
            pass

        bot.send_photo(
            chat_id,
            image_file,
            caption=f"✨ Готово!\n\n📝 {prompt}"
        )

    except Exception as e:
        print("IMAGE GENERATION ERROR:", repr(e))
        try:
            bot.edit_message_text(
                f"❌ Ошибка при генерации изображения.\n\nПричина: {str(e)[:800]}",
                chat_id,
                status_message.message_id
            )
        except Exception:
            bot.reply_to(status_message, "❌ Ошибка при генерации изображения.")


# =========================================================
# /TERMS и /PAYSUPPORT
# =========================================================

@bot.message_handler(commands=["terms"])
def terms(message):
    bot.reply_to(
        message,
        "📄 Условия использования AptekaAI\n\n"
        "AptekaAI предоставляет доступ к текстовому ИИ и генерации изображений.\n\n"
        "Цифровые услуги оплачиваются Telegram Stars.\n\n"
        "Перед оплатой пользователь видит стоимость услуги.\n\n"
        "По вопросам оплаты используйте /paysupport."
    )


@bot.message_handler(commands=["paysupport"])
def payment_support(message):
    bot.reply_to(
        message,
        "💳 Поддержка по оплате\n\n"
        "Если возникла проблема с оплатой или приобретённой услугой, "
        "напишите владельцу бота.\n\n"
        "Укажите, пожалуйста, время оплаты и что именно не сработало."
    )


# =========================================================
# ОБЫЧНЫЙ ТЕКСТОВЫЙ ИИ
# =========================================================

@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    if not message.text:
        return

    user_id = message.from_user.id
    user_text = message.text.strip()

    # В группах отвечаем только на упоминание или reply
    BOT_USERNAME = bot.get_me().username
    is_group = message.chat.type in ["group", "supergroup"]
    is_mentioned = BOT_USERNAME and f"@{BOT_USERNAME}" in user_text
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == bot.get_me().id
    )

    if is_group and not (is_mentioned or is_reply_to_bot):
        return

    # Убираем @username
    clean_text = user_text
    if BOT_USERNAME:
        clean_text = clean_text.replace(f"@{BOT_USERNAME}", "").strip()

    if not clean_text:
        bot.reply_to(message, "Я здесь! Чем могу помочь?")
        return

    # Проверка лимитов
    if not is_owner(user_id):
        user = get_user(user_id)

        if not user["unlimited"]:
            if user["messages"] >= DAILY_FREE_MESSAGES:
                bot.reply_to(
                    message,
                    f"🚫 Ты использовал {DAILY_FREE_MESSAGES} бесплатных сообщений сегодня.\n\n"
                    f"⭐ Купи безлимит за {UNLIMITED_PRICE_STARS} Stars:\n/buy"
                )
                return

            # Увеличиваем счётчик
            new_count = user["messages"] + 1
            update_user_messages(user_id, new_count)

    # Быстрый ответ на привет
    if clean_text.lower() in ["привет", "привееет", "приветик", "hi", "hello"]:
        bot.reply_to(message, "Привет! Я AptekaAI 🤖\nЧем могу помочь?")
        return

    # Запрос к ИИ
    bot.send_chat_action(message.chat.id, "typing")

    try:
        url = "https://api.proxyapi.ru/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты — полезный, умный и вежливый ИИ-ассистент AptekaAI. "
                        "Отвечай понятно, грамотно и дружелюбно на русском языке."
                    )
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
            bot.reply_to(message, f"❌ Ошибка ИИ.\nКод: {response.status_code}")

    except Exception as e:
        print("TEXT ERROR:", repr(e))
        bot.reply_to(message, "❌ Ошибка соединения с ИИ.")


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":
    render_url = os.environ.get("RENDER_EXTERNAL_URL")

    if render_url:
        bot.remove_webhook()
        bot.set_webhook(
            url=f"{render_url.rstrip('/')}/{TELEGRAM_TOKEN}"
        )

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
