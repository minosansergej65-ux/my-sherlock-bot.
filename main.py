import telebot
import subprocess

# Новый токен успешно добавлен, привязка к PuzzleBot сброшена!
TOKEN = '8836578040:AAGYmbBxH2Ohp16v2FYL-U7hm-p0Zx6h3lE'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне никнейм, и я найду его профили в соцсетях через Sherlock.")

@bot.message_handler(func=lambda message: True)
def search_username(message):
    username = message.text.strip()
    
    if " " in username:
        bot.reply_to(message, "Пожалуйста, введите один никнейм без пробелов.")
        return

    bot.reply_to(message, f"Ищу профили для: {username}...\nПоиск в облаке занимает около 1 минуты.")
    
    try:
        # Запуск Sherlock в облачной системе Linux
        result = subprocess.run(
            ["sherlock", username, "--timeout", "5"], 
            capture_output=True, 
            text=True,
            errors='ignore'
        )
        
        lines = result.stdout.split('\n')
        found_links = [line for line in lines if "http" in line]
        
        if found_links:
            response = "Вот что удалось найти:\n\n" + "\n".join(found_links)
        else:
            response = "Профилей с таким именем не найдено."
            
    except Exception as e:
        response = f"Ошибка поиска: {e}"
        
    bot.send_message(message.chat.id, response)

if __name__ == '__main__':
    print("Бот запущен на сервере!")
    bot.infinity_polling()
