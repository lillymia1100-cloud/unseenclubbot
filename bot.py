
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = "https://unseenclubbot.netlify.app/"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Open Channel",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "👇 Click the button below to open the Web App.",
        reply_markup=reply_markup
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in Render Environment Variables")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
