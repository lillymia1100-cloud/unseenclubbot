import os
import json
import threading
import asyncio
import psycopg

from flask import Flask, jsonify
from flask_cors import CORS

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

DATABASE_URL = os.getenv("DATABASE_URL")

web = Flask(__name__)
CORS(web)

# =========================
# POSTS DATABASE
# =========================

def load_posts():

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set")

    with psycopg.connect(DATABASE_URL) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, title, thumb, links, created_at
                FROM posts_new
                ORDER BY created_at DESC
                LIMIT 100
            """)

            rows = cur.fetchall()

    posts = []

    for row in rows:

        posts.append({
            "id": row[0],
            "title": row[1] or "",
            "thumb": row[2] or "",
            "links": row[3] or []
        })

    return posts
def save_post(post):

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set")

    with psycopg.connect(DATABASE_URL) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO posts_new
                (title, thumb, links)
                VALUES (%s, %s, %s)
            """, (
                post["title"],
                post["thumb"],
                json.dumps(post["links"])
            ))

        conn.commit()
# =========================
# BATCH NOTIFICATION
# =========================

pending_notifications = 0
notification_task = None
notification_lock = asyncio.Lock()


async def send_batch_notification(bot):

    global pending_notifications

    await asyncio.sleep(10)

    async with notification_lock:

        count = pending_notifications
        pending_notifications = 0

    if count <= 0:
        return

    if count == 1:
        text = (
            "1 New Post Uploaded! ✔\n\n"
            "Tap below to view"
        )
    else:
        text = (
            f"{count} New Posts Uploaded! ✔\n\n"
            "Tap below to view"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Open Channel",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Backup Channel",
                url="https://t.me/+hOT3oXhwGyxmNjA1"
            )
        ]
    ]

    with psycopg.connect(DATABASE_URL) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT user_id
                FROM bot_users
            """)

            users = cur.fetchall()

    print(
        f"📢 Sending notification to {len(users)} users"
    )

    for row in users:

        user_id = row[0]

        try:

            await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

            await asyncio.sleep(0.05)

        except Exception as e:

            print(
                "❌ Notification failed:",
                user_id,
                e
            )


async def schedule_notification(bot):

    global notification_task

    if notification_task is None or notification_task.done():

        notification_task = asyncio.create_task(
            send_batch_notification(bot)
        )

# =========================
# WEB APP API
# =========================

@web.route("/")
def home():
    return "UnseenClub Bot is running."


@web.route("/health")
def health():
    return "OK"


@web.route("/api/posts")
def api_posts():

    posts = load_posts()

    return jsonify({
        "posts": posts,
        "count": len(posts)
    })
# =========================
# TELEGRAM THUMBNAIL PROXY
# =========================

from urllib.request import urlopen
import json as json_module

@web.route("/api/thumb/<file_id>")
def thumbnail(file_id):

    if not BOT_TOKEN:
        return "BOT_TOKEN is not set", 500

    try:

        # Get Telegram file information
        info_url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
            f"?file_id={file_id}"
        )

        with urlopen(info_url) as response:

            data = json_module.loads(
                response.read().decode("utf-8")
            )

        if not data.get("ok"):
            return "Telegram file not found", 404

        file_path = data["result"]["file_path"]

        # Download image from Telegram
        file_url = (
            f"https://api.telegram.org/file/bot"
            f"{BOT_TOKEN}/{file_path}"
        )

        with urlopen(file_url) as response:

            image_data = response.read()

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "image/jpeg"
                )
            )

        return image_data, 200, {
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=86400"
        }

    except Exception as e:

        print("THUMBNAIL ERROR:", e)

        return "Thumbnail error", 500

# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        [
            InlineKeyboardButton(
                "📱 Open Channel",
                web_app=WebAppInfo(
                    url=WEB_APP_URL
                )
            )
        ]
    ]

    await update.message.reply_text(
        "🎉 Welcome!\n\n"
        "👇 Click the button below to open the Web App.",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )
async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    with psycopg.connect(DATABASE_URL) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO bot_users
                (user_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
            """, (
                user.id,
                user.username,
                user.first_name
            ))

        conn.commit()

    keyboard = [
        [
            InlineKeyboardButton(
    "📱 Open Channel",
    web_app=WebAppInfo(
        url="https://unseenclubbot.netlify.app/"
    )
)
        ],
        [
            InlineKeyboardButton(
                "📢 Backup Channel",
                url="https://t.me/+hOT3oXhwGyxmNjA1"
            )
        ]
    ]

    await update.message.reply_text(
        "🎉 Welcome!\n\n"
        "👇 Choose where to view",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    print(
        "✅ USER SAVED:",
        user.id,
        user.username
    )

# =========================
# CHANNEL POSTS
# =========================

async def channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    post = update.channel_post

    new_post = {
        "id": post.message_id,
        "title": "",
        "thumb": "",
        "links": []
    }

    # =========================
    # TEXT / CAPTION
    # =========================

    text = post.text or post.caption or ""

    new_post["title"] = text

    print("CHANNEL TEXT/CAPTION:", text)

    # =========================
    # EXTRACT LINKS
    # =========================

    for word in text.split():

        if word.startswith("http://") or word.startswith("https://"):

            new_post["links"].append(word)

            print("CHANNEL LINK:", word)

    # =========================
    # PHOTO
    # =========================

    if post.photo:

        photo = post.photo[-1]

        print("CHANNEL PHOTO:", photo.file_id)

        new_post["thumb"] = photo.file_id

    # =========================
    # VIDEO
    # =========================

    elif post.video:

        print("CHANNEL VIDEO:", post.video.file_id)

        new_post["thumb"] = post.video.file_id

    # =========================
    # DOCUMENT
    # =========================

    elif post.document:

        print(
            "CHANNEL DOCUMENT:",
            post.document.file_id
        )

    print("FINAL POST:", new_post)

    # =========================
    # SAVE TO DATABASE
    # =========================

    save_post(new_post)

    # =========================
    # BATCH NOTIFICATION
    # =========================

    global pending_notifications

    async with notification_lock:

        pending_notifications += 1

    await schedule_notification(context.bot)

    print(
        "✅ POST SAVED PERMANENTLY:",
        new_post["id"]
    )

    print(
        "📢 PENDING NOTIFICATIONS:",
        pending_notifications
    )
# =========================
# WEB SERVER
# =========================

def run_web():

    web.run(
        host="0.0.0.0",
        port=PORT
    )


# =========================
# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN is not set"
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST,
            channel_post
        )
    )

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    print(
        "🌐 Web server started on port",
        PORT
    )

    print(
        "🤖 Bot is running..."
    )

    print(
        "📣 Channel post listener is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
