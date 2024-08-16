from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='sol_cost'),
            KeyboardButton(text="get_latest_coin")
        ],
        [
            KeyboardButton(text="check_trades"),
            KeyboardButton(text="/")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="choose action from menu",
    selective=True
)
