import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import yt_dlp

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
user_links = {}

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Привет! Отправь ссылку на YouTube-видео, и я предложу варианты для скачивания.")

@dp.message_handler()
async def handle_link(msg: types.Message):
    url = msg.text.strip()
    if not url.startswith("http"):
        await msg.reply("Пожалуйста, пришли корректную ссылку.")
        return

    user_links[msg.from_user.id] = url
    buttons = []
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            seen = set()
            for fmt in formats:
                height = fmt.get("height")
                filesize = fmt.get("filesize")
                if height in [360, 480, 720, 1080] and height not in seen and filesize:
                    seen.add(height)
                    text = f"{height}p — {fmt.get('width')}x{fmt.get('height')} ({round(filesize/1024/1024, 1)} MB)"
                    buttons.append(InlineKeyboardButton(text, callback_data=f"dl_{height}"))

        if not buttons:
            await msg.reply("Не удалось найти форматы для загрузки.")
        else:
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(*buttons)
            await msg.reply("Выберите качество:", reply_markup=kb)
    except Exception as e:
        await msg.reply(f"Ошибка: {e}")

@dp.callback_query_handler(lambda c: c.data.startswith("dl_"))
async def download_quality(callback: types.CallbackQuery):
    height = int(callback.data.split("_")[1])
    url = user_links.get(callback.from_user.id)
    if not url:
        await callback.answer("Ссылка не найдена. Отправь её снова.")
        return
    out_name = f"video_{callback.from_user.id}_{height}p.mp4"
    try:
        ydl_opts = {
            'format': f'bestvideo[height={height}]+bestaudio/best[height={height}]',
            'outtmpl': out_name,
            'merge_output_format': 'mp4',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await bot.send_chat_action(callback.from_user.id, action=types.ChatActions.UPLOAD_VIDEO)
        await bot.send_video(callback.from_user.id, open(out_name, 'rb'))
        os.remove(out_name)
    except Exception as e:
        await callback.message.answer(f"Ошибка при загрузке: {e}")
    await callback.answer()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp)

