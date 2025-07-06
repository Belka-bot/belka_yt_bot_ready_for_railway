import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from dotenv import load_dotenv
from downloader import list_formats, download_format
from yandex_uploader import upload_to_yandex

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Пришли ссылку на видео — я дам кнопки с форматами.")

@dp.message(F.text & ~F.command)
async def handle_link(message: types.Message):
    url = message.text.strip()
    formats = list_formats(url)
    kb = InlineKeyboardMarkup()
    for f in formats:
        kb.add(
            InlineKeyboardButton(
                f["format"],
                callback_data=f"dl:{f['format_id']}"
            )
        )
    await message.answer("Выберите формат:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("dl:"))
async def handle_download(cb: types.CallbackQuery):
    fmt = cb.data.split(":", 1)[1]
    await cb.message.answer("Скачиваю...")
    filepath = download_format(cb.message.text, fmt)
    size_mb = os.path.getsize(filepath) / 1024**2

    if size_mb <= 50:
        await cb.message.answer_document(open(filepath, "rb"))
    else:
        link = upload_to_yandex(filepath)
        await cb.message.answer(
            f"Файл слишком большой. Скачай через Яндекс.Диск: {link}"
        )

    await cb.message.delete_reply_markup()

async def on_startup(app: web.Application):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))

async def on_cleanup(app: web.Application):
    await bot.delete_webhook()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    web.run_app(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )