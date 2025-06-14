import os
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

TOKEN = os.environ["TOKEN"]

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.chat.id
    user_links[user_id] = url

    ydl_opts = {}
    formats_info = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        for f in info['formats']:
            if f.get('height') in [360, 480, 720, 1080] and f.get('filesize'):
                label = f"{f['height']}p — {f['resolution']} ({round(f['filesize'] / 1024 / 1024, 1)} MB)"
                formats_info.append(InlineKeyboardButton(label, callback_data=f"{f['format_id']}"))        

    if formats_info:
        markup = InlineKeyboardMarkup([[b] for b in formats_info])
        await update.message.reply_text("Выберите качество:", reply_markup=markup)
    else:
        await update.message.reply_text("Качество не найдено.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    format_id = query.data
    user_id = query.message.chat.id
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("Ошибка: URL не найден.")
        return

    filename = f"{user_id}_{int(time.time())}.mp4"
    ydl_opts = {
        "format": format_id,
        "outtmpl": filename,
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": "cookies.txt"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    with open(filename, "rb") as f:
        await context.bot.send_video(chat_id=user_id, video=f)

    os.remove(filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
