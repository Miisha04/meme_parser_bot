import json
import asyncio
import websockets
import time
from aiogram import F, Router, types
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command, CommandStart
from aiogram.utils.formatting import Text, Bold
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards import main_kb
from parser import get_data_from_pumpfun

router = Router()


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


@router.message(F.text.lower() == 'get_latest_coin')
async def get_latest_coin(message: Message):
    url = "https://frontend-api.pump.fun/coins/latest"
    text = get_data_from_pumpfun(url)

    if text is None:
        await message.answer("Failed to retrieve data from the API.")
        return

    try:
        data = json.loads(text)
        token = data.get('mint')
        name = data.get('name')
        twitter = data.get('twitter')
        telegram = data.get('telegram')
        website = data.get('website')
        market_cap = data.get('market_cap')
        img = data.get('image_uri')

        await message.answer(
            "Info about coin:\n\n"
            f"Address: {token}\n"
            f"Name: {name}\n"
            f"Twitter: {twitter}\n"
            f"Telegram: {telegram}\n"
            f"Website: {website}\n"
            f"MC: {market_cap} sol\n"
            f"{img}\n"
        )
    except json.JSONDecodeError:
        await message.answer("Failed to parse JSON data.")


@router.message(F.text == 'check_tokens')
async def check_tokens(message: Message):
    good_tokens = {}
    await message.answer("WebSocket listener started.")
    url = "wss://rpc.api-pump.fun/ws"
    async with websockets.connect(url) as ws:
        payload = {
            "method": "subscribeTrades",
        }
        await ws.send(json.dumps(payload))
        async for trade in ws:
            try:
                data = json.loads(trade)
                mint_address = data.get('Mint')
                sol_amount = data.get('SolAmount') / 1000000000

                if (sol_amount > 2.5) and (data.get('IsBuy')):

                    if mint_address in good_tokens:
                        good_tokens[mint_address] += sol_amount
                    else:
                        good_tokens[mint_address] = sol_amount

                    copy_good_tokens = good_tokens

                    for key, value in copy_good_tokens.items():
                        if value > 10:
                            token_text = get_data_from_pumpfun(f"https://frontend-api.pump.fun/coins/{key}")
                            token_data = json.loads(token_text)

                            await message.answer(
                                f"Solana value: {value}\n"
                                f"Mint Address: <code>{key}</code>\n"
                                f"MC: {token_data.get('usd_market_cap')} usd\n"
                                f"Name_token: {token_data.get('name')}\n",
                                parse_mode="HTML"
                            )

                        print(f"Key: {key}, Value: {value}")



                    print("\n")
                    # await message.answer(
                    #     f"Solana Amount: {sol_amount}\n"
                    #     f"Mint Address: <code>{mint_address}</code>\n"
                    #     f"User Wallet: {data.get('User')}\n"
                    #     f"MC: {token_data.get('usd_market_cap')} usd\n"
                    #     f"Name_token: {token_data.get('name')}\n",
                    #     parse_mode="HTML"
                    #
                    # )
            except TelegramNetworkError as e:
                print(f"Network error: {e}. Retrying...")
                break


@router.callback_query(lambda c: c.data == "stop_check")
async def handle_stop(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup()  # Убираем кнопки
    await callback_query.answer("Останавливаю процесс.  ..")