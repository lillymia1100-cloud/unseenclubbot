import os
import threading

from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = "https://unseenclubbot.netlify.app/"
PORT = int(os.getenv("PORT", "10000"))

web = Flask(__name__)


@web.route("/")
def home():
    return "Bot is running!"


@web.route("/health")
def health():
    return "OK"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Open Channel",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ]

    await update.message.reply_text(
        "🎉 Welcome!\n\n"
        "👇 Click the button below to open the Web App.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post

    if post.text:
        print("CHANNEL TEXT:", post.text)

    elif post.caption:
        print("CHANNEL CAPTION:", post.caption)

    elif post.video:
        print("CHANNEL VIDEO:", post.video.file_id)

    elif post.photo:
        print("CHANNEL PHOTO:", post.photo[-1].file_id)

    elif post.document:
        print("CHANNEL DOCUMENT:", post.document.file_id)

    else:
        print("CHANNEL POST RECEIVED")


def run_web():
    web.run(
        host="0.0.0.0",
        port=PORT
    )


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            channel_post
        )
    )

    # Start web server for Render
    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    print("🌐 Web server started on port", PORT)
    print("🤖 Bot is running...")
    print("📣 Channel post listener is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
