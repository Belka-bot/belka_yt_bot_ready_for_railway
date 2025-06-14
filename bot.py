
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from yt_dlp import YoutubeDL

TOKEN = os.environ["TOKEN"]

# Словарь для хранения ссылок по chat_id
pending_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео, и я его скачаю!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    # Клавиатура с выбором качества
    keyboard = [
        [InlineKeyboardButton("360p", callback_data=f"360|{url}")],
        [InlineKeyboardButton("720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("1080p", callback_data=f"1080|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите качество:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice, url = query.data.split("|")
    chat_id = query.message.chat_id

    await query.edit_message_text("Скачиваю видео...")

    quality = {
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    }[choice]

    ydl_opts = {
        "format": quality,
        "outtmpl": f"{chat_id}_{int(time.time())}.mp4",
        "merge_output_format": "mp4",
        "quiet": True,
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        "cookiefile": "cookies.txt"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = ydl_opts["outtmpl"]
        with open(filename, "rb") as f:
            await context.bot.send_video(chat_id=chat_id, video=f)

        os.remove(filename)
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Ошибка: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
