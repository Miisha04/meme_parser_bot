import asyncio
import logging

from aiogram import Bot, Dispatcher
from handlers import router
from config import TOKEN
from aiohttp_socks import ProxyType, ProxyConnector

# Настройки прокси
proxy_host = '45.159.180.71'
proxy_port = 13840
login = 'user132834'
password = 'gyckq8'

# Создаем подключение через SOCKS5 прокси
proxy_url = f'socks5://{login}:{password}@{proxy_host}:{proxy_port}'

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
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
