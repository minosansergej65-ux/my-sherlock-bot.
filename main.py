import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import g4f

# ТВОЙ НОВЫЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# КОМАНДА /START
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "🤖 **Привет! Я твой новый, стабильный ИИ-помощник.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я создал изображение!"
    )
    await message.reply(welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@dp.message(Command("img"))
async def handle_image_generation(message: types.Message):
    prompt = message.text.replace('/img', '').strip()
    
    if not prompt:
        await message.reply("❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img красивый пейзаж`")
        return
        
    await message.reply(f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 5-10 секунд.", parse_mode="Markdown")
    
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nofeed=true"
        
        await bot.send_photo(chat_id=message.chat.id, photo=image_url, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        await message.reply(f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# УМНЫЙ И СТАБИЛЬНЫЙ ЧАТ С ИИ
@dp.message()
async def handle_ai_chat(message: types.Message):
    user_text = message.text.strip()
    
    if not user_text:
        return

    # Показываем статус "печатает"
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Чистый, вежливый и безопасный системный промпт
        system_prompt = (
            "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, "
            "грамотно и дружелюбно на русском языке. Не используй нецензурную лексику.\n"
            "Запрос пользователя: " + user_text
        )

        # Бесплатный авто-подбор рабочего провайдера нейросети
        response = await asyncio.to_thread(
            g4f.ChatCompletion.create,
            model=g4f.models.default,
            messages=[{"role": "user", "content": system_prompt}]
        )
        
        ai_response = response if response else "Извините, нейросеть задумалась. Попробуйте отправить сообщение еще раз."
        await message.reply(ai_response)
        
    except Exception as e:
        await message.reply("Извините, не удалось получить ответ. Попробуйте перефразировать вопрос.")

async def main():
    # Удаляем старый вебхук, чтобы включить быстрый polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
