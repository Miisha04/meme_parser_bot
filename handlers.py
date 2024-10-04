import json
import asyncio
import aiohttp
import re

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards import main_kb

router = Router()

good_tokens = {}
bad_tokens = []
stop_event = asyncio.Event()
sorted_tokens = {}

# Данные для прокси
PROXY_HOST = "45.159.180.71"
PROXY_PORT = 3840
LOGIN = "user132834"
PASSWORD = "gyckq8"


@router.message(CommandStart())
async def get_start(message: Message):
    await message.answer(f"Hello, {message.from_user.first_name}", reply_markup=main_kb)


@router.message(Command("help"))
async def get_help(message: Message):
    await message.answer("it's help command")


async def decrement_values_periodically():
    while True:
        await asyncio.sleep(300)  # Ждем 5 минут

        for key, token_info in list(good_tokens.items()):
            token_info["volume"] -= 0.5
            if token_info["volume"] <= 0:
                del good_tokens[key]  # Удаляем токен, если его объем стал отрицательным

        print("Values decremented by 0.5")


def extract_first_word(message):
    """Функция для извлечения первого слова в квадратных скобках"""
    match = re.search(
        r'\["(\w+)"', message
    )  # Ищем первое слово внутри квадратных скобках
    if match:
        return match.group(1)
    return None


async def check_trades(message: Message):
    url = "wss://frontend-api.pump.fun/socket.io/?EIO=4&transport=websocket"
    proxy_auth = aiohttp.BasicAuth(LOGIN, PASSWORD)
    proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"

    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(url, proxy=proxy_url, proxy_auth=proxy_auth) as ws:
                    await ws.send_str("40")  # Отправляем сообщение "40"
                    print("Сообщение '40' отправлено")
                    await message.answer("пошла возня")

                    # Запускаем задачи для отправки сообщения '3' и декрементации
                    heartbeat_task = asyncio.create_task(send_heartbeat(ws))
                    decrement_task = asyncio.create_task(decrement_values_periodically())

                    await check_trades_logic(ws, message)

                    # Завершаем фоновые задачи, если основная задача завершилась
                    heartbeat_task.cancel()
                    decrement_task.cancel()

            except aiohttp.ClientConnectionError as e:
                await message.answer(f"Ошибка подключения: {e}")
                print("Переподключение через 5 секунд...")
                await asyncio.sleep(5)  # Ждем перед переподключением

            except Exception as e:
                await message.answer(f"Неизвестная ошибка: {e}")
                break  

async def send_heartbeat(ws):
    """Функция для отправки сообщения '3' каждые 10 секунд."""
    while True:
        await asyncio.sleep(10)  # Ждем 10 секунд

        try:
            if not ws.closed:  # Проверяем, что соединение не закрыто
                await ws.send_str("3")
                print("Отправлено сообщение '3'")
            else:
                print("Соединение закрыто, не могу отправить сообщение")
                break  # Прерываем цикл, если соединение закрыто
        except aiohttp.ClientConnectionError as e:
            print(f"Ошибка соединения: {e}")
            break  # Прерываем цикл в случае ошибки соединения
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            break  # Прерываем цикл в случае любой другой ошибки


async def check_trades_logic(ws, message):
    stop_button = InlineKeyboardBuilder()
    stop_button.add(types.InlineKeyboardButton(text="Stop", callback_data="stop_check"))

    if not stop_event.is_set():
        await message.reply(
            "Нажми кнопку чтобы остановить возню", reply_markup=stop_button.as_markup()
        )

    stop_event.clear()

    asyncio.create_task(decrement_values_periodically())

    while True:
        if stop_event.is_set():
            await message.answer("возня кончилась")
            return  # Завершение функции

        try:
            result = await ws.receive()

            if isinstance(result, aiohttp.WSMessage):
                if result.type == aiohttp.WSMsgType.TEXT:
                    result_str = result.data
                else:
                    print(f"Неожиданный тип сообщения: {result.type}")
                    raise TypeError(f"Неподдерживаемый тип данных: {result.type}")
            else:
                print(f"Получено сообщение не в формате строки: {result}")
                raise TypeError("Неподдерживаемый формат данных")

            first_word = extract_first_word(result_str)
            if first_word == "tradeCreated":
                match = re.search(r'42\["tradeCreated",({.*})\]', result_str)
                if match:
                    json_data = match.group(1)
                    try:
                        data = json.loads(json_data)
                        is_buy = data.get("is_buy")
                        sol_amount = data.get("sol_amount") / 1000000000
                        mint_address = data.get("mint")

                        if mint_address not in bad_tokens:

                            if sol_amount > 0.2:
                                if is_buy:
                                    if mint_address in good_tokens:
                                        good_tokens[mint_address]["txs_buy"] += 1
                                        good_tokens[mint_address]["volume"] += sol_amount
                                    else:
                                        good_tokens[mint_address] = {
                                            "volume": sol_amount,
                                            "hits": 0,
                                            "txs_buy": 1,
                                            "txs_sell": 0,
                                        }

                                    if good_tokens[mint_address]["volume"] > 15:
                                        good_tokens[mint_address]["hits"] += 1

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

                                        # Добавляем кнопку "fuck this" для каждого токена
                                        token_buttons = InlineKeyboardBuilder()
                                        token_buttons.add(
                                            types.InlineKeyboardButton(
                                                text="fuck this",
                                                callback_data=f"bad_token_{mint_address}",
                                            )
                                        )

                                        await message.answer_photo(
                                            photo=img,  # URL картинки
                                            caption=(
                                                f"<strong>Name</strong>: {token_name} — <a href='https://x.com/search?q=%24{token_symbol}&src=typed_query'><strong>${token_symbol}</strong></a> | (<strong>{good_tokens[mint_address]['hits']}</strong>)\n"
                                                f"<strong>Volume surge</strong>: {sol_surge} SOL under 5 mins\n\n"  # кол-во минут зависит от периода во сколько раз отнимается 0.5
                                                f"<strong>Market Cap</strong>: ${market_cap_usdt}\n"
                                                f"<strong>CA</strong>: <code>{mint_address}</code>\n\n"
                                                f"<a href='{twitter}'>Twitter</a> | <a href='{telegram}'>Telegram</a> | <a href='{website}'>Website</a> | <a href='https://solscan.io/account/{creator}'>Creator (solscan)</a> | <a href='https://pump.fun/profile/{creator}'>Creator PF</a>\n\n"
                                                f"<strong>Description</strong>: {token_description}\n\n"
                                                f"<a href='https://t.me/achilles_trojanbot?start=r-bankx0-{mint_address}'>Trojan</a> | <a href='{trade_link}'>GmGn</a> | <a href='https://photon-sol.tinyastro.io/en/lp/{mint_address}'>Photon</a> | <a href='https://bullx.io/terminal?chainId=1399811149&address={mint_address}'>BullX</a>"
                                            ),
                                            parse_mode="HTML",  # Указываем HTML форматирование для текста
                                            reply_markup=token_buttons.as_markup(),  # Кнопки
                                        )

                                        good_tokens[mint_address]["volume"] = 0
                                else:
                                    if mint_address in good_tokens:
                                        good_tokens[mint_address]["volume"] -= sol_amount
                                        good_tokens[mint_address]["txs_sell"] += 1
                                        if good_tokens[mint_address]["volume"] <= 0:
                                            del good_tokens[mint_address]

                                sorted_tokens = dict(sorted(good_tokens.items(), key=lambda item: item[1]['volume'], reverse=True))
                                print(sorted_tokens, end='\n\n\n')

                    except json.JSONDecodeError:
                        print(f"Ошибка декодирования JSON: {json_data}")

        except Exception as e:
            print(f"Ошибка: {e}")
            break


@router.message(Command("check_trades"))
async def check_trades_command(message: Message):
    await check_trades(message)


@router.callback_query(lambda c: c.data == "stop_check")
async def handle_stop(callback_query: types.CallbackQuery):
    stop_event.set()  # Устанавливаем событие, чтобы остановить цикл
    await callback_query.message.edit_reply_markup()  # Убираем кнопки
    await callback_query.answer("Останавливаю процесс...")


@router.callback_query(lambda c: c.data.startswith("bad_token_"))
async def handle_bad_token(callback_query: types.CallbackQuery):
    token_id = callback_query.data.split("_")[-1]  # Получаем идентификатор токена
    if token_id not in bad_tokens:
        bad_tokens.append(token_id)
        await callback_query.message.edit_reply_markup()
        await callback_query.answer("Токен добавлен в список плохих")

        for token in bad_tokens:
            print(token)

        # print("\n\n")
        # print(good_tokens)

        # print("\n")
