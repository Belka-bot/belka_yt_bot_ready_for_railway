
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TOKEN")

quality_buttons = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь мне ссылку на видео с YouTube.")

def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T"]:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} P{suffix}"

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Скачиваю информацию о видео...")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            buttons = []
            quality_buttons[update.effective_chat.id] = {}

            seen = set()
            for fmt in formats:
                height = fmt.get('height')
                fsize = fmt.get('filesize')
                url = fmt.get('url')
                if not height or not fsize or not url:
                    continue
                if height in seen:
                    continue
                seen.add(height)

                label = f"{height}p — {fmt['width']}x{height} ({sizeof_fmt(fsize)})"
                callback_data = f"{height}|{fmt['url']}"

                buttons.append([InlineKeyboardButton(label, callback_data=callback_data)])
                quality_buttons[update.effective_chat.id][str(height)] = fmt['url']

            if buttons:
                await update.message.reply_text("Выберите качество:", reply_markup=InlineKeyboardMarkup(buttons))
            else:
                await update.message.reply_text("Не удалось найти подходящие форматы.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    height, video_url = query.data.split("|")

    await query.message.reply_text(f"Скачиваю {height}p...")
    await context.bot.send_video(chat_id=query.message.chat.id, video=video_url)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
