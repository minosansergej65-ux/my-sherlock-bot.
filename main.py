import telebot
import requests
from openai import OpenAI

# ТВОЙ ТОКЕН ТЕЛЕГРАМ (УЖЕ ВСТАВЛЕН)
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'
# ТВОЙ ОФИЦИАЛЬНЫЙ КЛЮЧ OPENAI (УЖЕ ВСТАВЛЕН)
OPENAI_API_KEY = 'sk-DM6qOt35yk3ZzFHGgqb8CqmtDZGJU8K8'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
BOT_USERNAME = bot.get_me().username

# Подключаем официальный клиент OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

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
    prompt = message.text.replace('/img', '').replace(f'@{BOT_USERNAME}', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img котик`")
        return
        
    bot.reply_to(message, f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 5-10 секунд.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        # Картинки генерируются без жесткой цензуры через Pollinations
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        
        img_data = requests.get(image_url).content
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# УМНЫЙ И ОФИЦИАЛЬНЫЙ ЧАТ С CHATGPT (БЕЗ ЖЕСТКОЙ ЦЕНЗУРЫ В ТЕМАХ)
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
        bot.reply_to(message, "Я здесь! Чем я могу вам помочь?")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Системная инструкция: бот адекватный, культурный, но без глупых этических блокировок в темах
        system_prompt = (
            "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, "
            "грамотно и дружелюбно на русском языке. Тебе разрешено обсуждать любые взрослые темы, "
            "но сам веди диалог культурно и без мата."
        )

        # Прямой и стабильный запрос к модели gpt-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_text}
            ],
            timeout=25
        )
        
        ai_response = response.choices[0].message.content.strip()
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка соединения с ИИ. Проверьте баланс ключа OpenAI. Детали: {e}")

if __name__ == '__main__':
    bot.delete_webhook()
    print("Официальный ChatGPT-бот запущен!")
    bot.infinity_polling()
