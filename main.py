import telebot
import requests
import os
import time
import g4f
import re
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
    return "Сервер ИИ-помощника с определителем номеров успешно работает!", 200

# КОМАНДА /START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой продвинутый ИИ-помощник.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я создал изображение!\n"
        "📞 **Проверка номера:** Просто отправь мне любой номер телефона (например, `+79991234567`), и я покажу легальную информацию о нем из открытых источников!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    BOT_USERNAME = bot.get_me().username
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img красивый пейзаж`")
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

# АВТОМАТИЧЕСКАЯ ФУНКЦИЯ ЛЕГАЛЬНОЙ ПРОВЕРКИ НОМЕРА ТЕЛЕФОНА
def check_phone_number(message, phone):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Очищаем номер от лишних символов (оставляем только цифры)
    clean_phone = re.sub(r'\D', '', phone)
    
    # Если номер начинается с 8, меняем на 7 для международной базы
    if len(clean_phone) == 11 and clean_phone.startswith('8'):
        clean_phone = '7' + clean_phone[1:]
        
    try:
        # Запрос к бесплатному открытому API для определения оператора и региона
        response = requests.get(f"https://rosreestr.online{clean_phone}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('data'):
                info = data['data']
                operator = info.get('operator', 'Неизвестен')
                region = info.get('region', 'Неизвестен')
                country = info.get('country', 'Неизвестна')
                
                # Формируем ссылки для безопасного легального поиска в один клик
                import urllib.parse
                search_query = urllib.parse.quote(f"кто звонил {phone}")
                google_link = f"https://google.com{search_query}"
                yandex_link = f"https://yandex.ru{search_query}"
                
                report = (
                    f"📞 **Информация о нове телефона {phone}:**\n\n"
                    f"🌐 **Страна:** {country}\n"
                    f"📍 **Регион:** {region}\n"
                    f"📱 **Официальный оператор:** {operator}\n\n"
                    f"🔎 **Искать отзывы о номере в открытых источниках:**\n"
                    f"🔗 [Проверить в Яндекс]({yandex_link})\n"
                    f"🔗 [Проверить в Google]({google_link})\n\n"
                    f"☝️ _Нейросеть не хранит скрытые персональные данные людей (паспорта, имена) ради безопасности и соблюдения закона РФ._"
                )
                bot.reply_to(message, report, parse_mode="Markdown", disable_web_page_preview=True)
                return True
        
        # Если API не ответило, создаем базовый ответ со ссылками
        import urllib.parse
        search_query = urllib.parse.quote(f"кто звонил {phone}")
        yandex_link = f"https://yandex.ru{search_query}"
        
        bot.reply_to(
            message, 
            f"🔎 Опеределитель региона временно недоступен, но вы можете проверить отзывы о номере {phone} в открытых источниках:\n\n"
            f"🔗 [Посмотреть отзывы в Яндекс]({yandex_link})",
            parse_mode="Markdown"
        )
        return True
    except:
        return False

# УМНЫЙ ЧАТ С ИИ И АВТО-ОПРЕДЕЛЕНИЕМ НОМЕРОВ
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

    # ПРОВЕРКА: Если пользователь отправил номер телефона (регулярное выражение для поиска номеров)
    phone_pattern = r'(?:\+?7|8)?[\s\(-]*?\d{3}[\s\)-]*?\d{3}[\s\-]*?\d{2}[\s\-]*?\d{2}'
    match = re.search(phone_pattern, clean_text)
    
    if match:
        # Если в тексте найден номер, запускаем легальный определитель
        phone_found = match.group()
        if len(re.sub(r'\D', '', phone_found)) >= 10: # Проверка, что это длинный номер, а не просто цифры
            check_phone_number(message, phone_found)
            return

    # Если это обычный текст — отправляем в ИИ
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        system_prompt = (
            "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, "
            "грамотно и дружелюбно на русском языке. Не используй нецензурную лексику.\n"
            "Запрос пользователя: " + clean_text
        )

        response = g4f.ChatCompletion.create(
            model=g4f.models.default, 
            messages=[{"role": "user", "content": system_prompt}],
        )
        
        ai_response = response if response else "Извините, сервер временно не ответил. Попробуйте отправить сообщение еще раз."
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения с ИИ. Детали: {e}")

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
