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
from  wallets_tokens_created import rugs_checker

router = Router()

good_tokens = {}
bad_tokens = []
stop_event = asyncio.Event()
sorted_tokens = {}




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
        print("Values decremented by 0.5")


def extract_first_word(message):
    """Функция для извлечения первого слова в квадратных скобках."""
    match = re.search(r'\["(\w+)"', message)
    return match.group(1) if match else None


async def send_heartbeat(ws):
    """Функция для отправки сообщения '3' каждые 10 секунд."""
    while not ws.closed:
        await asyncio.sleep(10)
        try:
            await ws.send_str("3")
            print("Отправлено сообщение '3'")
        except aiohttp.ClientConnectionError as e:
            print(f"Ошибка соединения: {e}")
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
            result = await ws.receive()

            if result.type == aiohttp.WSMsgType.TEXT:
                first_word = extract_first_word(result.data)
                if first_word == "tradeCreated":
                    match = re.search(r'42\["tradeCreated",({.*})\]', result.data)
                    if match:
                        data = json.loads(match.group(1))
                        await process_trade(data, message)
            else:
                print(f"Неожиданный тип сообщения: {result.type}")

        except Exception as e:
            print(f"Ошибка: {e}")
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
                if floor(token_info["volume"] // 15) > token_info["hits"]:
                    token_info["hits"] += 1
                    await send_token_alert(mint_address, token_info, data, message)
            else:
                token_info["txs_sell"] += 1
                token_info["volume"] -= sol_amount
                if token_info["volume"] <= 0:
                    del good_tokens[mint_address]

    global sorted_tokens
    #sorted_tokens = dict(sorted(good_tokens.items(), key=lambda item: item[1]["volume"], reverse=True))
    #print(sorted_tokens)


async def send_token_alert(mint_address, token_info, data, message):
    """Функция для отправки информации о токене."""
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
    token_name = data.get("name")
    token_symbol = data.get("symbol")
    market_cap_usdt = round(
        data.get("usd_market_cap", 0)
    )
    trade_link = (
        f"https://gmgn.ai/sol/token/{mint_address}"
    )
    website = data.get("website")
    img = data.get("image_uri")
    sol_surge = round(
        good_tokens[mint_address]["volume"], 2
    )

    try:
        await message.answer_photo(
            photo=img,  # URL картинки
            caption=(
                f"{token_name} — <a href='https://x.com/search?q=%24{token_symbol}&src=typed_query&f=live'><strong>${token_symbol}</strong></a> | <strong>Hits</strong>: {good_tokens[mint_address]['hits']}\n"
                f"Volume surged {sol_surge} SOL under 5 mins\n"
                f"<strong>Buys:</strong> {good_tokens[mint_address]['txs_buy']} | <strong>Sells:</strong> {good_tokens[mint_address]['txs_sell']}\n\n"
                f"<strong>Market Cap</strong>: ${market_cap_usdt}\n"
                f"<strong>CA</strong>: <code>{mint_address}</code>\n"
                f"<strong>Description</strong>: {token_description}\n"
                f"<a href='{twitter}'>Twitter</a> | <a href='{telegram}'>Telegram</a> | <a href='{website}'>Website</a>\n\n"
                f"<strong>Creator Tab: </strong>\n"
                f"Balance: {creator_balance(creator)} SOL | Token Supply: 0.00% | {rugs_checker(creator)}\n"
                f"<a href='https://solscan.io/account/{creator}'>Solscan</a> | <a href='https://pump.fun/profile/{creator}'>Pump Fun</a>\n\n"
                f"Top Holders: soon\n\n"
                f"<a href='https://t.me/achilles_trojanbot?start=r-bankx0-{mint_address}'>Trojan</a> | <a href='{trade_link}'>GmGn</a> | <a href='https://photon-sol.tinyastro.io/en/lp/{mint_address}'>Photon</a> | <a href='https://bullx.io/terminal?chainId=1399811149&address={mint_address}'>BullX</a>"
            ),
            parse_mode="HTML",  # Указываем HTML форматирование для текста
            reply_markup=token_buttons.as_markup(),  # Кнопки
        )
    except Exception as e:
        print(f"Ошибка отправки изображения: {e}")
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
                f"Balance: {creator_balance(creator)} SOL | Token Supply: 0.00% | {rugs_checker(creator)}\n"
                f"<a href='https://solscan.io/account/{creator}'>Solscan</a> | <a href='https://pump.fun/profile/{creator}'>Pump Fun</a>\n\n"
                f"Top Holders: soon\n\n"
                f"<a href='https://t.me/achilles_trojanbot?start=r-bankx0-{mint_address}'>Trojan</a> | <a href='{trade_link}'>GmGn</a> | <a href='https://photon-sol.tinyastro.io/en/lp/{mint_address}'>Photon</a> | <a href='https://bullx.io/terminal?chainId=1399811149&address={mint_address}'>BullX</a>"
            ),
            parse_mode="HTML",  # Указываем HTML форматирование
            reply_markup=token_buttons.as_markup(),  # Добавляем кнопки
        )


@router.message(Command("check_trades"))
async def check_trades_command(message: Message):
    url = "wss://frontend-api.pump.fun/socket.io/?EIO=4&transport=websocket"
    proxy_auth = aiohttp.BasicAuth(LOGIN, PASSWORD)
    proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url, proxy=proxy_url, proxy_auth=proxy_auth) as ws:
            await ws.send_str("40")
            print("Сообщение '40' отправлено")

            await asyncio.gather(
                send_heartbeat(ws),
                decrement_values_periodically(),
                check_trades_logic(ws, message)
            )
