import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

STATE_NAME, STATE_REQUEST, STATE_TIME = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Я Юлия — психолог и арт-терапевт.\n\n"
        "Рада, что вы написали. Давайте познакомимся — как вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STATE_NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        f"Приятно познакомиться, {context.user_data['name']}! 🌿\n\n"
        "Расскажите вкратце — с чем хотите прийти на консультацию?\n"
        "(Можно написать пару слов или подробнее — как вам удобно)"
    )
    return STATE_REQUEST


async def got_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["request"] = update.message.text.strip()
    await update.message.reply_text(
        "Поняла. Последний вопрос — в какое время вам удобно встретиться?\n"
        "Например: утром, вечером в будни, по выходным…"
    )
    return STATE_TIME


async def got_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["time"] = update.message.text.strip()

    name = context.user_data["name"]
    request = context.user_data["request"]
    time = context.user_data["time"]

    user = update.effective_user
    tg_link = f"@{user.username}" if user.username else f"tg://user?id={user.id}"

    # Уведомление для Юлии
    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    admin_text = (
        "🌸 <b>Новая заявка с сайта</b>\n\n"
        f"<b>Имя:</b> {esc(name)}\n"
        f"<b>Запрос:</b> {esc(request)}\n"
        f"<b>Удобное время:</b> {esc(time)}\n"
        f"<b>Telegram:</b> {esc(tg_link)}"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        parse_mode="HTML",
    )

    # Ответ клиенту
    await update.message.reply_text(
        f"Спасибо, {name}! Ответы записала 🌿\n\n"
        "Напишу вам с аккаунта @juulymart, чтобы подтвердить запись 🫶"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Хорошо, до встречи! Если захотите записаться — просто напишите /start")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            STATE_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_request)],
            STATE_TIME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, got_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
