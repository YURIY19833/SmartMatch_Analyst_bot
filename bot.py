import telebot

# Импортируем нашу готовую функцию прогноза из соседнего файла
from predict import predict_match

# Telegram bot token should come from the environment for security.
# Set TELEGRAM_TOKEN in Render or your local .env file.
import os

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN is not set. Please set it in environment variables."
    )

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🤖 **Привет! Я твой персональный AI-аналитик футбольных матчей.**\n\n"
        "Я умею подключаться к базе данных, оценивать форму команд и рассчитывать вероятности исходов с помощью модели Random Forest.\n\n"
        "📝 **Как получить прогноз:**\n"
        "Отправь мне названия двух команд через дефис или слово `vs`.\n"
        "Разделитель обязателен, чтобы я не запутался в названиях из нескольких слов.\n\n"
        "📌 *Примеры:*\n"
        "`liverpool - chelsea`\n"
        "`manchester united vs arsenal`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def handle_prediction_request(message):
    text = message.text.strip()

    # Определяем разделитель (дефис или "vs")
    if " vs " in text.lower():
        teams = text.lower().split(" vs ")
    elif "-" in text:
        teams = text.split("-")
    else:
        bot.reply_to(
            message,
            "⚠️ Не вижу разделителя! Напиши команды через дефис или `vs`.\n"
            "Пример: `liverpool - chelsea`",
        )
        return

    # Очищаем названия от лишних пробелов
    home_team = teams[0].strip()
    away_team = teams[1].strip()

    # Отправляем статус "печатает", пока модель думает и ходит в базу
    bot.send_chat_action(message.chat.id, "typing")

    # Вызываем наш готовый инференс
    prediction_result = predict_match(home_team, away_team)

    # Отправляем красивый ответ пользователю
    bot.reply_to(message, prediction_result, parse_mode="Markdown")


if __name__ == "__main__":
    print("🚀 Бот успешно запущен и слушает серверы Telegram...")
    bot.infinity_polling()
