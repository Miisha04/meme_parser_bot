import json
import asyncio
import aiohttp
import re
from math import floor
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import main_kb
from config import PROXY_HOST, PROXY_PORT, LOGIN, PASSWORD
from creatorBalance import creator_balance
from wallets_tokens_created import rugs_checker
#from top10holders_and_dev import get_creator_balance, get_top_10_holder_rate, cto_checker

import logging

router = Router()

good_tokens = {}
bad_tokens = set()  # Множество для хранения плохих токенов
stop_event = asyncio.Event()
sorted_tokens = {}

trade_created_pattern = re.compile(r'42\["tradeCreated",({.*})\]')
first_word_pattern = re.compile(r'\["(\w+)"')


MIN_SOL_VOLUME = 15

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@router.message(CommandStart())
async def get_start(message: Message):
    await message.answer(f"Hello, {message.from_user.first_name}", reply_markup=main_kb)


@router.message(Command("help"))
async def get_help(message: Message):
    await message.answer("it's help command")


async def decrement_values_periodically():
    """Асинхронная функция для периодического уменьшения значений volume."""
    while True:
        await asyncio.sleep(300)  # Ждем 5 минут
        for token_info in good_tokens.values():
            token_info["volume"] -= 0.5
        logging.info("Values decremented by 0.5")


def extract_first_word(message):
    """Извлекает первое слово в квадратных скобках из сообщения."""
    match = first_word_pattern.search(message)
    return match.group(1) if match else None


async def send_heartbeat(ws):
    """Функция для отправки сообщения '3' каждые 10 секунд."""
    while not ws.closed:
        await asyncio.sleep(10)
        try:
            await ws.send_str("3")
            logging.info("Отправлено сообщение '3'")
        except aiohttp.ClientConnectionError as e:
            logging.error(f"Ошибка соединения при отправке heartbeat: {e}")
            break


async def check_trades_logic(ws, message):
    stop_button = InlineKeyboardBuilder()
    stop_button.add(types.InlineKeyboardButton(text="Stop", callback_data="stop_check"))

    if not stop_event.is_set():
        await message.reply(
            "Нажми кнопку чтобы остановить возню", reply_markup=stop_button.as_markup()
        )

    stop_event.clear()

    while not stop_event.is_set():
        try:
            result = await ws.receive(timeout=30)  # Указываем тайм-аут для ожидания сообщений
            if result.type == aiohttp.WSMsgType.TEXT:
                first_word = extract_first_word(result.data)
                if first_word == "tradeCreated":
                    match = trade_created_pattern.search(result.data)
                    if match:
                        data = json.loads(match.group(1))
                        asyncio.create_task(process_trade(data, message))  # Асинхронная обработка трейдов
            else:
                logging.warning(f"Неожиданный тип сообщения: {result.type}")
        except asyncio.TimeoutError:
            logging.warning("Тайм-аут при ожидании сообщения от вебсокета.")
        except Exception as e:
            logging.error(f"Ошибка при обработке сообщения: {e}")
            break


async def process_trade(data, message):
    mint_address = data.get("mint")
    sol_amount = data.get("sol_amount", 0) / 1_000_000_000

    if mint_address not in bad_tokens:
        if sol_amount > 0.2:
            token_info = good_tokens.setdefault(mint_address, {
                "volume": 0, "txs_buy": 0, "txs_sell": 0, "hits": 0
            })

            if data.get("is_buy"):
                token_info["txs_buy"] += 1
                token_info["volume"] += sol_amount
                if floor(token_info["volume"] // MIN_SOL_VOLUME) > token_info["hits"]:
                    token_info["hits"] += 1
                    asyncio.create_task(send_token_alert(mint_address, token_info, data, message))  # Асинхронная отправка уведомлений
            else:
                token_info["txs_sell"] += 1
                token_info["volume"] -= sol_amount
                if token_info["volume"] <= 0:
                    del good_tokens[mint_address]

    global sorted_tokens
    sorted_tokens = dict(sorted(good_tokens.items(), key=lambda item: item[1]["volume"], reverse=True))
    logging.info(f"Текущие отсортированные токены: {sorted_tokens}")


async def send_token_alert(mint_address, token_info, data, message):
    """Асинхронная функция для отправки информации о токене."""
    token_name = data.get("name")
    token_symbol = data.get("symbol")
    trade_link = f"https://gmgn.ai/sol/token/{mint_address}"

    token_buttons = InlineKeyboardBuilder()
    token_buttons.add(
        types.InlineKeyboardButton(text="fuck this", callback_data=f"bad_token_{mint_address}")
    )

    twitter = data.get("twitter")
    telegram = data.get("telegram")
    creator = data.get("creator")
    token_description = data.get("description")
    market_cap_usdt = round(data.get("usd_market_cap", 0))
    website = data.get("website")
    img = data.get("image_uri")
    sol_surge = round(good_tokens[mint_address]["volume"], 2)
    #dev_balance = await asyncio.to_thread(get_creator_balance, mint_address)  # Асинхронный вызов в отдельном потоке

    try:
        await message.answer_photo(
            photo=img,
            caption=(
                f"{token_name} — <a href='https://x.com/search?q=%24{token_symbol}&src=typed_query&f=live'><strong>${token_symbol}</strong></a> | <strong>Hits</strong>: {good_tokens[mint_address]['hits']}\n"
                f"Volume surged {sol_surge} SOL under 5 mins\n"
                f"<strong>Buys:</strong> {good_tokens[mint_address]['txs_buy']} | <strong>Sells:</strong> {good_tokens[mint_address]['txs_sell']}\n\n"
                f"<strong>Market Cap</strong>: ${market_cap_usdt}\n"
                f"<strong>CA</strong>: <code>{mint_address}</code>\n"
                f"<strong>Description</strong>: {token_description}\n"
                f"<a href='{twitter}'>Twitter</a> | <a href='{telegram}'>Telegram</a> | <a href='{website}'>Website</a>\n\n"
                f"<strong>Creator Tab: </strong>\n"
                #f"Balance: {creator_balance(creator)} SOL | Token Supply: {dev_balance} | {rugs_checker(creator)}\n"
                f"<a href='https://solscan.io/account/{creator}'>Solscan</a> | <a href='https://pump.fun/profile/{creator}'>Pump Fun</a>\n\n"
                #f"Top Holders: {get_top_10_holder_rate(mint_address)} | CTO: {cto_checker(sol_surge, dev_balance)}\n\n"
                f"<a href='https://t.me/achilles_trojanbot?start=r-bankx0-{mint_address}'>Trojan</a> | <a href='{trade_link}'>GmGn</a> | <a href='https://photon-sol.tinyastro.io/en/lp/{mint_address}'>Photon</a> | <a href='https://bullx.io/terminal?chainId=1399811149&address={mint_address}'>BullX</a>"
            ),
            parse_mode="HTML",
            reply_markup=token_buttons.as_markup(),
        )
    except Exception as e:
        logging.error(f"Ошибка отправки изображения: {e}")
        await message.answer(
            text=(
                f"{token_name} — <a href='https://x.com/search?q=%24{token_symbol}&src=typed_query&f=live'><strong>${token_symbol}</strong></a> | <strong>Hits</strong>: {good_tokens[mint_address]['hits']}\n"
                f"Volume surged {sol_surge} SOL under 5 mins\n"
                f"<strong>Buys:</strong> {good_tokens[mint_address]['txs_buy']} | <strong>Sells:</strong> {good_tokens[mint_address]['txs_sell']}\n\n"
                f"<strong>Market Cap</strong>: ${market_cap_usdt}\n"
                f"<strong>CA</strong>: <code>{mint_address}</code>\n"
                f"<strong>Description</strong>: {token_description}\n"
                f"<a href='{twitter}'>Twitter</a> | <a href='{telegram}'>Telegram</a> | <a href='{website}'>Website</a>\n\n"
                f"<strong>Creator Tab: </strong>\n"
                #f"Balance: {creator_balance(creator)} SOL | Token Supply: {dev_balance} | {rugs_checker(creator)}\n"
                f"<a href='https://solscan.io/account/{creator}'>Solscan</a> | <a href='https://pump.fun/profile/{creator}'>Pump Fun</a>\n\n"
                #f"Top Holders: {get_top_10_holder_rate(mint_address)} | CTO: {cto_checker(sol_surge, dev_balance)}\n\n"
                f"<a href='https://t.me/achilles_trojanbot?start=r-bankx0-{mint_address}'>Trojan</a> | <a href='{trade_link}'>GmGn</a> | <a href='https://photon-sol.tinyastro.io/en/lp/{mint_address}'>Photon</a> | <a href='https://bullx.io/terminal?chainId=1399811149&address={mint_address}'>BullX</a>"
            ),
            parse_mode="HTML",
            reply_markup=token_buttons.as_markup(),
        )


@router.message(Command("check_trades"))
async def check_trades_command(message: Message):
    url = "wss://frontend-api.pump.fun/socket.io/?EIO=4&transport=websocket"
    proxy_auth = aiohttp.BasicAuth(LOGIN, PASSWORD)
    proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, proxy=proxy_url, proxy_auth=proxy_auth) as ws:
            await ws.send_str("40")
            logging.info("Сообщение '40' отправлено")

            await asyncio.gather(
                send_heartbeat(ws),
                decrement_values_periodically(),
                check_trades_logic(ws, message)
            )
