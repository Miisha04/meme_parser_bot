import json
import asyncio
import websockets

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from parser import get_data_from_pumpfun
from config import bot

from keyboards import main_kb
router = Router()

good_tokens = {}
bad_tokens = []
stop_event = asyncio.Event()
bad_token_event = asyncio.Event()

CHAT_IDD = 601718316


@router.message(CommandStart())
async def get_start(message: Message):
    await message.answer(f"Hello, {message.from_user.first_name}", reply_markup=main_kb)


@router.message(Command("help"))
async def get_help(message: Message):
    await message.answer("it`s help command")


@router.message(F.text.lower() == 'sol_cost')
async def get_sol_price(message: Message):
    url = "https://frontend-api.pump.fun/sol-price"
    text = get_data_from_pumpfun(url)

    if text is None:
        await message.answer("Failed to retrieve data from the API.")
        return

    try:
        data = json.loads(text)
        await message.answer(f"Current Solana cost: {data.get('solPrice')}")
    except json.JSONDecodeError:
        await message.answer("Failed to parse JSON data.")


async def decrement_values_periodically():
    while True:
        await asyncio.sleep(300)  # Ждем 5 минут

        for key in good_tokens:
            good_tokens[key] -= 0.5

        print("Values decremented by 0.5")


async def subscribe_trades(ws, message):

    payload = {
        "method": "subscribeTrades"
    }
    await ws.send(json.dumps(payload))
    print("Subscribed to trades")


async def unsubscribe_trades(ws, message):

    payload = {
        "method": "unsubscribeTrades"
    }
    await ws.send(json.dumps(payload))
    print("Unsubscribed from trades")


<<<<<<< HEAD
stop_event = asyncio.Event()


async def decrement_values_periodically():
    while True:
        await asyncio.sleep(300)  # Ждем 5 минут

        for key in good_tokens:
            good_tokens[key] -= 0.5

        print("Values decremented by 0.5")


=======
>>>>>>> bec7bfe4bfb40a57c1e3263fc0c217e4b950a283
async def check_trades_logic(ws, message):
    stop_button = InlineKeyboardBuilder()
    stop_button.add(types.InlineKeyboardButton(
        text="Stop",
        callback_data="stop_check")
    )
    await message.reply(
        "Нажми кнопку чтобы остановить возню",
        reply_markup=stop_button.as_markup()
    )

    stop_event.clear()
    bad_token_event.clear()
    asyncio.create_task(decrement_values_periodically())

    asyncio.create_task(decrement_values_periodically())

    while True:
        if stop_event.is_set():
            await unsubscribe_trades(ws, message)
            await message.answer("возня кончилась")
            break

        try:
            trade = await ws.recv()
            data = json.loads(trade)
            mint_address = data.get('Mint')
            sol_amount = data.get('SolAmount') / 1000000000

            if mint_address not in bad_tokens:
                if sol_amount > 0.4:
                    if data.get('IsBuy'):
                        if mint_address in good_tokens:
                            good_tokens[mint_address] += sol_amount
                        else:
                            good_tokens[mint_address] = sol_amount

                        del_key = ""

                        for key, value in good_tokens.items():
                            if value > 20:
                                token_text = get_data_from_pumpfun(f"https://frontend-api.pump.fun/coins/{key}")

                                if token_text is not None:
                                    token_data = json.loads(token_text)
                                    del_key = key
                                    trade_link = f"https://t.me/achilles_trojanbot?start=r-bankx0-{key}"

                                    await message.answer(
                                        f"Volume Surge: {round(value, 2)} SOL\n\n"
                                        f"Token name: {token_data.get('name')} (${token_data.get('symbol')})\n"
                                        f"Market Cap: ${round(token_data.get('usd_market_cap'), 0)}\n\n"
                                        f"CA: <code>{key}</code>\n\n"
                                        f"TG: {token_data.get('telegram')}\n"
                                        f"Twitter: {token_data.get('twitter')}\n"
                                        f"Website: {token_data.get('website')}\n\n"
                                        f"Trade link: {trade_link}\n"
                                        f"<a href='{token_data.get('image_uri')}'>IMG</a>",
                                        parse_mode="HTML"
                                    )

                                    # Создаем кнопку для пометки токена как "плохого"
                                    bad_token_button = InlineKeyboardBuilder()
                                    bad_token_button.add(types.InlineKeyboardButton(
                                        text="Fuck this",
                                        callback_data=f"bad_token_{key}")
                                    )
                                    await message.answer(
                                        "Нажми кнопку чтобы ебать токен",
                                        reply_markup=bad_token_button.as_markup()
                                    )

                                else:
                                    del_key = key
                                    await message.answer(
                                        f"Volume Surge: {round(value, 2)} SOL\n\n"
                                        f"CA: <code>{key}</code>\n",
                                        parse_mode="HTML"
                                    )
                            elif value < 0:
                                del_key = key

                        if del_key != "":
                            del good_tokens[del_key]

                    else:
<<<<<<< HEAD
                        good_tokens[mint_address] = sol_amount

                    del_key = ""

                    for key, value in good_tokens.items():
                        if value > 20:
                            token_text = get_data_from_pumpfun(f"https://frontend-api.pump.fun/coins/{key}")
                            token_data = json.loads(token_text)

                            del_key = key

                            await message.answer(
                                f"Volume Surge: {round(value, 2)} SOL\n\n"
                                f"Token name: {token_data.get('name')} (${token_data.get('symbol')})\n"
                                f"Market Cap: ${round(token_data.get('usd_market_cap'), 0)}\n\n"
                                f"CA: <code>{key}</code>\n"
                                f"<a href='{token_data.get('image_uri')}'>IMG</a>"
                                f"TG: {token_data.get('telegram')}\n"
                                f"Twitter: {token_data.get('twitter')}\n"
                                f"Website: {token_data.get('website')}\n",
                                parse_mode="HTML"
                            )

                        elif value < 0:
                            del_key = key

                        #print(f"Key: {key}, Value: {value}")

                    if del_key != "":
                        del good_tokens[del_key]

                    #print("\n")
                else:
                    if mint_address in good_tokens:
                        good_tokens[mint_address] -= sol_amount
=======
                        if mint_address in good_tokens:
                            good_tokens[mint_address] -= sol_amount
>>>>>>> bec7bfe4bfb40a57c1e3263fc0c217e4b950a283

        except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as e:
            print(f"Connection closed: {e}. Reconnecting...")
            await asyncio.sleep(5)
            continue


<<<<<<< HEAD
@router.message(Command('check_trades'))
=======
@router.message(Command("check_trades"))
>>>>>>> bec7bfe4bfb40a57c1e3263fc0c217e4b950a283
async def check_trades(message: Message):
    url = "wss://rpc.api-pump.fun/ws"
    async with websockets.connect(url) as ws:
        await message.answer("пошла возня")
        await subscribe_trades(ws, message)
        await check_trades_logic(ws, message)


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

        print("\n")
