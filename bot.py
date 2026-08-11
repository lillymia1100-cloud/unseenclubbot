import os

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


# =========================
# START COMMAND
# =========================

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
        "🎉 Welcome!\n\n"
        "👇 Click the button below to open the Web App.",
        reply_markup=reply_markup
    )


# =========================
# CHANNEL POSTS
# =========================

async def channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    post = update.channel_post

    if post.text:
        print("CHANNEL TEXT:", post.text)

    elif post.caption:
        print("CHANNEL CAPTION:", post.caption)

    elif post.video:
        print(
            "CHANNEL VIDEO:",
            post.video.file_id
        )

    elif post.photo:
        print(
            "CHANNEL PHOTO:",
            post.photo[-1].file_id
        )

    elif post.document:
        print(
            "CHANNEL DOCUMENT:",
            post.document.file_id
        )

    else:
        print("CHANNEL POST RECEIVED")


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN is not set in Render Environment Variables"
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Telegram Channel Posts
    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            channel_post
        )
    )

    print("🤖 Bot is running...")
    print("📣 Channel post listener is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
