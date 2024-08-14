import asyncio
import logging

from aiogram import Bot, Dispatcher

from handlers import router
from config import TOKEN


bot = Bot(TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)  # не дает копиться стартовым апдейтам
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")