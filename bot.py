import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import yt_dlp

TOKEN = os.environ.get("TOKEN")

user_video_data = {}

def get_keyboard(formats):
    buttons = []
    added = set()
    for f in formats:
        height = f.get("height")
        filesize = f.get("filesize")
        resolution = f.get("resolution")
        if height and filesize and height not in added:
            size_mb = round(filesize / 1024 / 1024, 1)
            label = f"{height}p — {resolution} ({size_mb} MB)"
            buttons.append([InlineKeyboardButton(label, callback_data=str(height))])
            added.add(height)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь ссылку на видео с YouTube.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("🔍 Обрабатываю ссылку...")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'extract_flat': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = [f for f in info["formats"] if f.get("filesize") and f.get("height")]
        formats.sort(key=lambda x: x.get("height"))

        user_video_data[update.effective_chat.id] = {
            "formats": formats,
            "title": info.get("title")
        }

        keyboard = get_keyboard(formats)
        await update.message.reply_text("Выберите качество:", reply_markup=keyboard)

async def handle_quality_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    height = int(query.data)

    video_data = user_video_data.get(query.message.chat.id)
    if not video_data:
        await query.edit_message_text("⚠️ Видео не найдено.")
        return

    format_info = next((f for f in video_data["formats"] if f.get("height") == height), None)
    if not format_info:
        await query.edit_message_text("⚠️ Формат недоступен.")
        return

    url = format_info["url"]
    filename = f"video_{height}p.mp4"

    ydl_opts = {
        'outtmpl': filename,
        'format': f"best[height={height}]",
    }

    await query.edit_message_text("⬇️ Скачиваю видео...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    with open(filename, "rb") as f:
        await context.bot.send_video(chat_id=query.message.chat.id, video=f, caption=video_data["title"])

    os.remove(filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(handle_quality_choice))
    app.run_polling()
