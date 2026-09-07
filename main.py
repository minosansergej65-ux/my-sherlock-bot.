message):
    welcome_text = (
        "🤖 Привет! Я твой продвинутый ИИ-бот.\n\n"
        "💬 **Общение:** Просто напиши мне любой вопрос, и я отвечу.\n"
        "🎨 **Картинки:** Напиши `/img` и описание на английском или русском "
        "(например: `/img котик в шляпе`), чтобы я сгенерировал изображение!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# КОМАНДА ДЛЯ ГЕНЕРАЦИИ КАРТИНКИ
@bot.message_handler(commands=['img'])
def handle_image_generation(message):
    # Забираем всё, что написано после команды /img
    prompt = message.text.replace('/img', '').strip()
    
    if not prompt:
        bot.reply_to(message, "❌ Пожалуйста, напишите описание картинки после команды. Пример: `/img красивый пейзаж`")
        return
        
    bot.reply_to(message, f"🎨 Рисую по вашему запросу: *\"{prompt}\"*...\nЭто займет около 10-20 секунд.", parse_mode="Markdown")
    bot.send_chat_action(message.chat.id, 'upload_photo')
    
    try:
        # Используем бесплатный быстрый генератор картинок Pollinations AI
        image_url = f"https://pollinations.ai{requests.utils.quote(prompt)}?width=1024&height=1024&seed=42&nofeed=true"
        
        # Скачиваем сгенерированную картинку
        img_data = requests.get(image_url).content
        
        # Отправляем фото пользователю в Telegram
        bot.send_photo(message.chat.id, img_data, caption=f"✨ Готово по запросу: {prompt}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Не удалось сгенерировать картинку. Ошибка: {e}")

# ОБЫЧНЫЙ ТЕКСТОВЫЙ ЧАТ С ИИ
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    user_text = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_text}],
        )
        ai_response = response.choices.message.content
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        bot.reply_to(message, f"Извините, сервер ИИ сейчас перегружен. Попробуйте еще раз. Ошибка: {e}")

if __name__ == '__main__':
    print("ИИ-Бот с генерацией картинок успешно запущен!")
    bot.infinity_polling()
