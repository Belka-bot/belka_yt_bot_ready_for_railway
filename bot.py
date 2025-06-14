import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import yt_dlp

TOKEN = os.environ["TOKEN"]
logging.basicConfig(level=logging.INFO)

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне ссылку на видео YouTube.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            buttons = []
            added = set()
            user_links[chat_id] = {}
            for f in formats:
                if f.get('ext') != 'mp4' or not f.get('filesize') or not f.get('height'):
                    continue
                quality = f"{f.get('height')}p"
                if quality in added:
                    continue
                added.add(quality)
                label = f"{quality} — {f['width']}x{f['height']} ({round(f['filesize'] / 1024 / 1024, 1)} MB)"
                user_links[chat_id][quality] = f['url']
                buttons.append([InlineKeyboardButton(label, callback_data=quality)])
            await update.message.reply_text("Выберите качество:", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    quality = query.data
    chat_id = query.message.chat_id
    video_url = user_links.get(chat_id, {}).get(quality)
    if video_url:
        await context.bot.send_video(chat_id=chat_id, video=video_url, caption=f"Вот ваше видео в {quality}")
    else:
        await query.edit_message_text("Не удалось найти ссылку.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
