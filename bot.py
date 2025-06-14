
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.effective_chat.id

    # Отправим "Скачиваю..."
    await update.message.reply_text("Скачиваю видео...")

    # Настройки yt_dlp
    ydl_opts = {
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'skip_download': True,
        'format': 'bestvideo+bestaudio/best',
    }

    # Список кнопок
    keyboard = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])

        for f in formats:
            if (
                f.get('height') in [360, 480, 720, 1080]
                and f.get('ext') == 'mp4'
                and f.get('filesize')
            ):
                height = f['height']
                size_mb = round(f['filesize'] / (1024 * 1024), 1)
                button = InlineKeyboardButton(
                    f"{height}p — {f['width']}x{height} ({size_mb} MB)",
                    callback_data=f"download|{f['format_id']}|{url}"
                )
                keyboard.append([button])

    # Отправляем кнопки
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выбери качество:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Не удалось получить форматы видео.")
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

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    url, format_id = data.split('|')

    ydl_opts = {
        'format': format_id,
        'outtmpl': f'video_{format_id}.mp4',
        'merge_output_format': 'mp4',
        'cookiefile': 'cookies.txt',
    }

    await query.edit_message_text("Скачиваю видео...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    with open(f'video_{format_id}.mp4', 'rb') as video:
        await context.bot.send_video(chat_id=query.message.chat.id, video=video)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    if data[0] == "download":
        format_id = data[1]
        url = data[2]

        await query.edit_message_text(text="Скачиваю выбранное качество...")

        ydl_opts = {
            'format': format_id,
            'outtmpl': 'video.mp4',
            'merge_output_format': 'mp4',
            'cookiefile': 'cookies.txt',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open("video.mp4", "rb")
        )

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = ydl_opts["outtmpl"]
        with open(video_path, 'rb') as f:
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
