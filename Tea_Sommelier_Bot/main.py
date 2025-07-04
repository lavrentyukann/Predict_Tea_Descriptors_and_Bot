from tea_sommelier_bot import TeaSommelierBot
from telegram_bot import TelegramBot
import logging

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    EXCEL_PATH = "../daochai_classified.xlsx"
    OLLAMA_URL = "http://192.168.0.32:8080/api/generate"
    MODEL_NAME = "gemma3:1b"
    # Инициализация чайного бота
    tea_bot = TeaSommelierBot(EXCEL_PATH, OLLAMA_URL, MODEL_NAME)

    # Токен Telegram бота
    TELEGRAM_TOKEN = "TOKEN"

    # Инициализация и запуск Telegram бота
    telegram_bot = TelegramBot(TELEGRAM_TOKEN, tea_bot)
    telegram_bot.run()