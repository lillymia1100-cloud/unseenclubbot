import os
import json
import threading
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
                SELECT id, title, thumb, links
                FROM posts
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
                INSERT INTO posts
                (id, title, thumb, links)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    thumb = EXCLUDED.thumb,
                    links = EXCLUDED.links
            """, (
                post["id"],
                post["title"],
                post["thumb"],
                json.dumps(post["links"])
            ))

        conn.commit()
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


# =========================
# CHANNEL POSTS
# =========================

async def channel_post(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    post = update.channel_post

    posts = load_posts()

    new_post = {
        "id": post.message_id,
        "title": "",
        "thumb": "",
        "links": []
    }

    # TEXT
    if post.text:

        new_post["title"] = post.text

        print(
            "CHANNEL TEXT:",
            post.text
        )

    # CAPTION
    elif post.caption:

        new_post["title"] = post.caption

        print(
            "CHANNEL CAPTION:",
            post.caption
        )

    # VIDEO
    if post.video:

        print(
            "CHANNEL VIDEO:",
            post.video.file_id
        )

        # Telegram file URL
        file = await context.bot.get_file(
            post.video.file_id
        )

        new_post["thumb"] = file.file_path

    # PHOTO
    elif post.photo:

        photo = post.photo[-1]

        print(
            "CHANNEL PHOTO:",
            photo.file_id
        )

        file = await context.bot.get_file(
            photo.file_id
        )

        new_post["thumb"] = file.file_path

    # DOCUMENT
    elif post.document:

        print(
            "CHANNEL DOCUMENT:",
            post.document.file_id
        )

    # Extract URLs from text/caption
    text = post.text or post.caption or ""

    words = text.split()

    for word in words:

        if (
            word.startswith("http://")
            or word.startswith("https://")
        ):
            new_post["links"].append(
                word
            )

    # If no link but video/photo exists,
    # use Telegram file URL
    if not new_post["links"] and new_post["thumb"]:

        new_post["links"] = [
            new_post["thumb"]
        ]

    # Add newest first
# Save post permanently in Supabase

save_post(new_post)

print(
    "✅ POST SAVED PERMANENTLY:",
    new_post["id"]
)
    # Save post permanently in Supabase

save_post(new_post)

print(
    "✅ POST SAVED PERMANENTLY:",
    new_post["id"]
)
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
            start
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
