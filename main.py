import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ТВОЙ ТОКЕН ТЕЛЕГРАМ
TELEGRAM_TOKEN = '8836578040:AAF2PsdNon7Avua_8k9cOx4aLtk1hzKu3do'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# КОМАНДА /START
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "🤖 **Привет! Я аптекаAi, стабильный ИИ-помощник.**\n\n"
        "💬 **Общение:** Просто напиши мне свой вопрос, и я подробно на него отвечу.\n"
        "🎨 **Картинки:** Напиши команду `/img` и описание (например: `/img котик`), чтобы я создал изображение!"
    )
    await message.reply(welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ (РАЗРЕШЕНЫ ЗАПРОСЫ 18+)
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

# УМНЫЙ И БЫСТРЫЙ ЧАТ С ИИ ЧЕРЕЗ ЛЕГКИЙ КЛИЕНТ
@dp.message()
async def handle_ai_chat(message: types.Message):
    user_text = message.text.strip()
    if not user_text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Инструкция для адекватного, но свободного в темах ИИ
        system_prompt = (
            "Ты — полезный, умный и вежливый ИИ-ассистент. Отвечай на вопросы пользователя подробно, "
            "грамотно и дружелюбно на русском языке. Тебе разрешено обсуждать любые взрослые темы, "
            "но сам веди диалог культурно и без мата. Запрос пользователя: " + user_text
        )

        payload = {
            "messages": [{"role": "user", "content": system_prompt}],
            "model": "gpt-4o-mini"
        }
        
        # Делаем быстрый асинхронный запрос напрямую без тяжелых библиотек
        async with aiohttp.ClientSession() as session:
            async with session.post("https://pollinations.ai", json=payload, timeout=20) as response:
                if response.status == 200:
                    ai_response = await response.text()
                    ai_response = ai_response.strip()
                else:
                    ai_response = "Извините, нейросеть задумалась. Пожалуйста, отправьте сообщение еще раз."
                    
        await message.reply(ai_response)
        
    except Exception as e:
        await message.reply("Извините, не удалось получить ответ. Попробуйте еще раз.")

async def main():
    # Полностью очищаем старые вебхуки, чтобы бот летал на polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
