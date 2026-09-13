import telebot
import requests
import os
import base64
import io
from flask import Flask, request
from datetime import date


# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_TOKEN = "8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do"
API_KEY = "sk-QYOX6VR8ZyC01vC4nB8V9kuTgWsQ4515"

OWNER_ID = 8948282169

# Укажи здесь username своего Telegram-канала
CHANNEL_USERNAME = "@apteka_mss323"

# Ссылка на канал для кнопки
CHANNEL_URL = "https://t.me/apteka_mss323"

UNLIMITED_PRICE_STARS = 100
IMAGE_PRICE_STARS = 20
DAILY_FREE_MESSAGES = 100


if not TELEGRAM_TOKEN:
    raise ValueError("Не найден TELEGRAM_TOKEN")

if not API_KEY:
    raise ValueError("Не найден PROXYAPI_KEY")


bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

users = {}
pending_images = {}


# =========================
# ПОЛЬЗОВАТЕЛИ
# =========================

def get_user(user_id):
    today = str(date.today())

    if user_id not in users:
        users[user_id] = {
            "date": today,
            "messages": 0,
            "unlimited": False
        }

    user = users[user_id]

    if user["date"] != today:
        user["date"] = today
        user["messages"] = 0

    return user


def is_owner(user_id):
    return user_id == OWNER_ID


# =========================
# ПРОВЕРКА ПОДПИСКИ
# =========================

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "creator",
            "administrator",
            "member"
        ]

    except Exception as e:
        print("SUBSCRIPTION CHECK ERROR:")
        print(repr(e))
        return False


def subscription_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()

    markup.add(
        telebot.types.InlineKeyboardButton(
            "📢 Подписаться на канал",
            url=CHANNEL_URL
        )
    )

    markup.add(
        telebot.types.InlineKeyboardButton(
            "✅ Я подписался",
            callback_data="check_subscription"
        )
    )

    return markup


def require_subscription(message):
    user_id = message.from_user.id

    # Владелец пользуется ботом без проверки
    if is_owner(user_id):
        return True

    # Проверяем подписку
    if is_subscribed(user_id):
        return True

    bot.send_message(
        message.chat.id,
        "🔒 Чтобы пользоваться AptekaAI, "
        "сначала подпишись на наш канал.\n\n"
        "После подписки нажми кнопку "
        "«✅ Я подписался».",
        reply_markup=subscription_keyboard()
    )

    return False


# =========================
# WEBHOOK
# =========================

@app.route("/" + TELEGRAM_TOKEN, methods=["POST"])
def getMessage():
    json_string = request.get_data().decode("utf-8")

    update = telebot.types.Update.de_json(
        json_string
    )

    bot.process_new_updates([update])

    return "!", 200


@app.route("/")
def index():
    return "AptekaAI server is running!", 200


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id

    # Если пользователь не подписан
    if not is_owner(user_id) and not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            "🔒 Добро пожаловать в AptekaAI!\n\n"
            "Чтобы пользоваться ботом, "
            "сначала подпишись на наш канал.\n\n"
            "После подписки нажми "
            "«✅ Я подписался».",
            reply_markup=subscription_keyboard()
        )
        return

    if is_owner(user_id):
        welcome_text = (
            "👑 Привет, владелец AptekaAI!\n\n"
            "У тебя полный бесплатный доступ.\n\n"
            "💬 Текстовый ИИ — без ограничений\n"
            "🎨 Генерация изображений — бесплатно\n\n"
            "Для картинки:\n"
            "/img кот в космосе"
        )

    else:
        welcome_text = (
            "🤖 Привет! Я AptekaAI.\n\n"
            "💬 Первые 100 сообщений в сутки — бесплатно.\n\n"
            "🎨 Генерация изображений "
            "оплачивается отдельно.\n\n"
            "Пример:\n"
            "/img реалистичный кот "
            "на крыше Парижа ночью\n\n"
            "⭐ После бесплатного лимита "
            "можно купить безлимитный "
            "текстовый доступ."
        )

    bot.reply_to(
        message,
        welcome_text
    )


# =========================
# КНОПКА ПРОВЕРКИ ПОДПИСКИ
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "check_subscription"
)
def check_subscription_callback(call):
    user_id = call.from_user.id

    if is_owner(user_id) or is_subscribed(user_id):

        bot.answer_callback_query(
            call.id,
            "✅ Подписка подтверждена!"
        )

        bot.send_message(
            call.message.chat.id,
            "🎉 Отлично! Подписка подтверждена.\n\n"
            "🤖 Теперь можешь пользоваться AptekaAI.\n\n"
            "Напиши свой вопрос или используй:\n"
            "/img — создать изображение\n"
            "/buy — купить безлимит"
        )

    else:

        bot.answer_callback_query(
            call.id,
            "❌ Ты ещё не подписан на канал.",
            show_alert=True
        )


# =========================
# ПОКУПКА БЕЗЛИМИТА
# =========================

@bot.message_handler(commands=["buy"])
def buy_unlimited(message):

    if not require_subscription(message):
        return

    user_id = message.from_user.id

    if is_owner(user_id):
        bot.reply_to(
            message,
            "👑 Ты владелец AptekaAI.\n"
            "У тебя безлимитный доступ бесплатно."
        )
        return

    bot.send_invoice(
        chat_id=message.chat.id,
        title="AptekaAI — безлимит",
        description=(
            "Безлимитные текстовые сообщения "
            "в AptekaAI без дневного ограничения."
        ),
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


# =========================
# ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ
# =========================

@bot.message_handler(commands=["img"])
def handle_image_generation(message):

    if not require_subscription(message):
        return

    user_id = message.from_user.id

    prompt = message.text.replace(
        "/img",
        "",
        1
    ).strip()

    if not prompt:
        bot.reply_to(
            message,
            "❌ Напиши описание картинки.\n\n"
            "Например:\n"
            "/img реалистичный кот "
            "на крыше Парижа ночью"
        )
        return

    # Владелец генерирует бесплатно
    if is_owner(user_id):

        bot.send_chat_action(
            message.chat.id,
            "upload_photo"
        )

        status_message = bot.reply_to(
            message,
            "👑 Владелец — бесплатно.\n"
            "🎨 Генерирую изображение..."
        )

        generate_image(
            chat_id=message.chat.id,
            prompt=prompt,
            status_message=status_message
        )

        return

    # Сохраняем запрос до оплаты
    pending_images[user_id] = {
        "prompt": prompt,
        "chat_id": message.chat.id
    }

    bot.send_invoice(
        chat_id=message.chat.id,
        title="AptekaAI — изображение",
        description=(
            "Одна генерация изображения "
            "через AptekaAI."
        ),
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


# =========================
# PRE-CHECKOUT
# =========================

@bot.pre_checkout_query_handler(
    func=lambda query: True
)
def process_pre_checkout(query):

    try:

        payload = query.invoice_payload

        if not (
            payload.startswith("image:")
            or payload.startswith("unlimited:")
        ):

            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Неизвестный заказ."
            )

            return

        bot.answer_pre_checkout_query(
            query.id,
            ok=True
        )

    except Exception as e:

        print("PRE-CHECKOUT ERROR:")
        print(repr(e))

        try:

            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Не удалось проверить заказ."
            )

        except Exception:
            pass


# =========================
# УСПЕШНАЯ ОПЛАТА
# =========================

@bot.message_handler(
    content_types=["successful_payment"]
)
def successful_payment(message):

    user_id = message.from_user.id

    payment = message.successful_payment

    payload = payment.invoice_payload

    print("================================")
    print("УСПЕШНАЯ ОПЛАТА")
    print("USER:", user_id)
    print("PAYLOAD:", payload)
    print("STARS:", payment.total_amount)
    print(
        "CHARGE ID:",
        payment.telegram_payment_charge_id
    )
    print("================================")

    # Безлимит
    if payload.startswith("unlimited:"):

        user = get_user(user_id)

        user["unlimited"] = True

        bot.reply_to(
            message,
            "✅ Оплата получена!\n\n"
            "⭐ Безлимитный текстовый "
            "доступ активирован.\n\n"
            "Теперь ты можешь писать ИИ "
            "без дневного лимита."
        )

        return

    # Изображение
    if payload.startswith("image:"):

        pending = pending_images.get(user_id)

        if not pending:

            bot.reply_to(
                message,
                "⚠️ Оплата получена, но запрос "
                "изображения не найден.\n\n"
                "Напиши /img ещё раз."
            )

            return

        prompt = pending["prompt"]

        chat_id = pending["chat_id"]

        del pending_images[user_id]

        status_message = bot.reply_to(
            message,
            "💳 Оплата получена!\n\n"
            "🎨 Генерирую изображение..."
        )

        generate_image(
            chat_id=chat_id,
            prompt=prompt,
            status_message=status_message
        )

        return


# =========================
# GENERATE IMAGE
# =========================

def generate_image(
    chat_id,
    prompt,
    status_message
):

    try:

        bot.send_chat_action(
            chat_id,
            "upload_photo"
        )

        url = (
            "https://api.proxyapi.ru/"
            "v1/images/generations"
        )

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

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=300
        )

        print(
            "PROXYAPI IMAGE STATUS:",
            response.status_code
        )

        print(
            "PROXYAPI IMAGE RESPONSE:",
            response.text[:2000]
        )

        if response.status_code != 200:

            try:

                bot.edit_message_text(
                    (
                        "❌ Ошибка генерации.\n\n"
                        f"Код: {response.status_code}\n\n"
                        f"{response.text[:1000]}"
                    ),
                    chat_id,
                    status_message.message_id
                )

            except Exception:

                bot.reply_to(
                    status_message,
                    "❌ Ошибка генерации изображения."
                )

            return

        result = response.json()

        if "data" not in result:
            raise Exception(
                "В ответе ProxyAPI отсутствует data"
            )

        if not result["data"]:
            raise Exception(
                "ProxyAPI вернул пустой результат"
            )

        if "b64_json" not in result["data"][0]:
            raise Exception(
                "В ответе отсутствует b64_json"
            )

        image_base64 = (
            result["data"][0]["b64_json"]
        )

        image_bytes = base64.b64decode(
            image_base64
        )

        image_file = io.BytesIO(
            image_bytes
        )

        image_file.name = "generated.jpg"

        try:

            bot.delete_message(
                chat_id,
                status_message.message_id
            )

        except Exception:
            pass

        bot.send_photo(
            chat_id,
            image_file,
            caption=(
                "✨ Готово!\n\n"
                f"📝 {prompt}"
            )
        )

    except Exception as e:

        print("================================")
        print("IMAGE GENERATION ERROR:")
        print(repr(e))
        print("================================")

        try:

            bot.edit_message_text(
                (
                    "❌ Ошибка при генерации "
                    "изображения.\n\n"
                    f"Причина: {str(e)[:1000]}"
                ),
                chat_id,
                status_message.message_id
            )

        except Exception:

            bot.reply_to(
                status_message,
                "❌ Ошибка при генерации изображения."
            )


# =========================
# УСЛОВИЯ
# =========================

@bot.message_handler(commands=["terms"])
def terms(message):

    if not require_subscription(message):
        return

    bot.reply_to(
        message,
        (
            "📄 Условия использования AptekaAI\n\n"
            "AptekaAI предоставляет доступ к "
            "текстовому ИИ и генерации изображений.\n\n"
            "Цифровые услуги оплачиваются "
            "Telegram Stars.\n\n"
            "Перед оплатой пользователь видит "
            "стоимость услуги.\n\n"
            "По вопросам оплаты используйте "
            "/paysupport."
        )
    )


# =========================
# ПОДДЕРЖКА
# =========================

@bot.message_handler(commands=["paysupport"])
def payment_support(message):

    if not require_subscription(message):
        return

    bot.reply_to(
        message,
        (
            "💳 Поддержка по оплате\n\n"
            "Если возникла проблема с оплатой "
            "или приобретённой услугой, "
            "напишите владельцу бота.\n\n"
            "Команда: /paysupport"
        )
    )


# =========================
# AI CHAT
# =========================

@bot.message_handler(
    func=lambda message: True
)
def handle_ai_chat(message):

    if not message.text:
        return

    user_id = message.from_user.id

    # Проверяем подписку перед использованием ИИ
    if not require_subscription(message):
        return

    user_text = message.text.strip()

    BOT_USERNAME = bot.get_me().username

    is_group = message.chat.type in [
        "group",
        "supergroup"
    ]

    is_mentioned = (
        BOT_USERNAME
        and f"@{BOT_USERNAME}" in user_text
    )

    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id
        == bot.get_me().id
    )

    # В группах отвечаем только на упоминание
    # или ответ на сообщение бота
    if is_group:

        if not (
            is_mentioned
            or is_reply_to_bot
        ):
            return

    clean_text = user_text

    if BOT_USERNAME:

        clean_text = clean_text.replace(
            f"@{BOT_USERNAME}",
            ""
        )

    clean_text = clean_text.strip()

    if not clean_text:

        bot.reply_to(
            message,
            "Я здесь! Чем могу помочь?"
        )

        return

    # Владелец — без лимита
    if is_owner(user_id):
        pass

    else:

        user = get_user(user_id)

        # Куплен безлимит
        if user["unlimited"]:
            pass

        else:

            # Проверяем дневной лимит
            if user["messages"] >= DAILY_FREE_MESSAGES:

                bot.reply_to(
                    message,
                    (
                        "🚫 Ты использовал "
                        "100 бесплатных сообщений сегодня.\n\n"
                        "⭐ Купи безлимит за "
                        f"{UNLIMITED_PRICE_STARS} Stars:\n\n"
                        "/buy"
                    )
                )

                return

            user["messages"] += 1

    # Быстрый ответ на приветствие
    if clean_text.lower() in [
        "привет",
        "привееет",
        "приветик",
        "hi",
        "hello"
    ]:

        bot.reply_to(
            message,
            "Привет! Я AptekaAI 🤖\n"
            "Чем могу помочь?"
        )

        return

    bot.send_chat_action(
        message.chat.id,
        "typing"
    )

    try:

        url = (
            "https://api.proxyapi.ru/"
            "v1/chat/completions"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        payload = {

            "model": "gpt-4o-mini",

            "messages": [

                {
                    "role": "system",
                    "content": (
                        "Ты — полезный, умный и "
                        "вежливый ИИ-ассистент "
                        "AptekaAI. "
                        "Отвечай понятно, грамотно "
                        "и дружелюбно на русском языке."
                    )
                },

                {
                    "role": "user",
                    "content": clean_text
                }
            ],

            "temperature": 0.7
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:

            result = response.json()

            ai_response = (
                result["choices"][0]
                ["message"]
                ["content"]
                .strip()
            )

            bot.reply_to(
                message,
                ai_response
            )

        else:

            print("TEXT API ERROR:")

            print(
                response.status_code
            )

            print(
                response.text
            )

            bot.reply_to(
                message,
                (
                    "❌ Ошибка ИИ.\n"
                    f"Код: {response.status_code}"
                )
            )

    except Exception as e:

        print("TEXT ERROR:")

        print(
            repr(e)
        )

        bot.reply_to(
            message,
            "❌ Ошибка соединения с ИИ."
        )


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":

    render_url = os.environ.get(
        "RENDER_EXTERNAL_URL"
    )

    if render_url:

        bot.remove_webhook()

        bot.set_webhook(
            url=(
                f"{render_url.rstrip('/')}"
                f"/{TELEGRAM_TOKEN}"
            )
        )

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
