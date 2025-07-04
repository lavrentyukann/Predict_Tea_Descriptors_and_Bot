import logging
from tea_sommelier_bot import TeaSommelierBot
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import asyncio

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class TelegramBot:
    def __init__(self, token: str, tea_bot: TeaSommelierBot):
        self.token = token
        self.tea_bot = tea_bot
        self.application = Application.builder().token(self.token).build()

        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Добавляем обработчик ошибок
        self.application.add_error_handler(self.error_handler)

    async def error_handler(self, update: object, context: CallbackContext) -> None:
        """Обработчик ошибок"""
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

        if update and hasattr(update, 'effective_chat'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
            )

    async def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я - Чайный Сомелье, готов помочь вам найти идеальный чай.\n\n"
            "Просто опишите, какой чай вы ищете: его тип, вкусовые ноты, "
            "предпочитаемую цену или другие характеристики.\n\n"
            "Примеры запросов:\n"
            "Улун с ванилью до 1500₽\n"
            "Красный чай из Юньнани\n"
            "Зеленый чай цветочный\n"
            "Выдержанный пуэр\n"
        )

        await update.message.reply_text(welcome_text)

    async def send_long_message(self, context: CallbackContext, chat_id: int, text: str, **kwargs):
        """Отправляет длинное сообщение частями по 4000 символов"""
        max_length = 4000  # Максимальная длина сообщения в Telegram
        for i in range(0, len(text), max_length):
            part = text[i:i + max_length]
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    **kwargs
                )
                # Добавляем небольшую задержку между сообщениями
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка при отправке части сообщения: {e}")

    async def help(self, update: Update, context: CallbackContext):
        """Обработчик команды /help"""
        help_text = (
            "🫖 <b>Как пользоваться ботом:</b>\n\n"
            "Просто напишите, какой чай вы ищете, например:\n"
            "- Улун с нотками ванили до 1500 рублей\n"
            "- Крепкий красный чай из Юньнани\n"
            "- Легкий зеленый чай с цветочными нотами\n"
            "- Выдержанный пуэр с землистыми нотами\n\n"
            "Я проанализирую ваш запрос и порекомендую подходящие варианты "
            "из нашей коллекции.\n\n"
            "Вы также можете уточнить:\n"
            "- Тип чая (зеленый, улун, пуэр и т.д.)\n"
            "- Вкусовые характеристики (цветочный, фруктовый, дымный и др.)\n"
            "- Ценовой диапазон (от/до)\n"
            "- Регион происхождения (если важно)\n"
            "- Наличие (только чаи в наличии)"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')

    async def handle_message(self, update: Update, context: CallbackContext, text: str = None):
        """Обработчик текстовых сообщений"""
        if text is None:
            if not hasattr(update, 'message') or not update.message:
                logger.error("Update doesn't contain message")
                return
            text = update.message.text

        chat_id = update.effective_chat.id

        try:
            # Отправляем сообщение о том, что бот думает
            if hasattr(update, 'message') and update.message:
                message = await update.message.reply_text("🔍 Ищу подходящие чаи...")
            else:
                message = await context.bot.send_message(chat_id, "🔍 Ищу подходящие чаи...")

            # Получаем рекомендации
            result = self.tea_bot.recommend_tea(text)

            if not result['recommendations']:
                await context.bot.send_message(chat_id,
                                               "К сожалению, не нашлось подходящих чаев по вашему запросу. Попробуйте изменить параметры поиска.", parse_mode='Markdown')
                return

            recommendation_text = self.__replace_markdown_with_emojis(result['recommendation_text'])

            # Отправляем развернутую рекомендацию
            await self.send_long_message(
                context,
                chat_id,
                recommendation_text,
                disable_web_page_preview=True,
                parse_mode='HTML'  # если нужно форматирование
            )

            # Отправляем краткую информацию о каждом чае
            for i, rec in enumerate(result['recommendations'], 1):
                tea_text = (
                    f"<b>Чай #{i}: {rec['title']}</b>\n"
                    f"💵 Цена: {rec['price']} руб.\n"
                    f"🏷 Категория: {', '.join(rec['tea_category'])}\n"
                    f"🛒 {'✅ Есть в наличии' if rec.get('available_tea', False) else '❌ Нет в наличии'}\n"
                    f"🔗 Ссылка: {rec.get('url', 'нет ссылки')}\n"
                )

                await self.send_long_message(
                    context,
                    chat_id,
                    tea_text,
                    disable_web_page_preview=True,
                    parse_mode='HTML'  # если нужно форматирование
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            await context.bot.send_message(
                chat_id,
                "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
            )

    def run(self):
        """Запуск бота"""
        self.application.run_polling()

    @staticmethod
    def __replace_markdown_with_emojis(text: str) -> str:
        replacements = {
            "**": "🍵",  # жирный
            "__": "✨",  # подчёркнутый
            "*": "🔸",  # курсив
            "# ": "🔷 ",  # заголовок
            "## ": "🔹 ",  # подзаголовок
            "### ": "▪️ ",  # под-подзаголовок
            "- ": "• ",  # список
            "> ": "💬 ",  # цитата
            "`": "🧠",  # код
        }

        for key, emoji in replacements.items():
            text = text.replace(key, emoji)
        return text
