import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from handlers import router
from config import TOKEN, PROXY_HOST, PROXY_PORT, LOGIN, PASSWORD
from aiohttp_socks import ProxyType, ProxyConnector


# Создаем подключение через SOCKS5 прокси
proxy_url = f'socks5://{LOGIN}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'

async def main():
    # Создаем бота с использованием прокси
    bot = Bot(token=TOKEN, proxy=proxy_url)
    dp = Dispatcher()

    dp.include_router(router)

    # Удаляем старые вебхуки
    await bot.delete_webhook(drop_pending_updates=True)

    # Начинаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Устанавливаем политику для совместимости с Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
