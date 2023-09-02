# pylint: disable=wrong-import-position

import datetime
import logging
from collections import defaultdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

initiated = []
processed = defaultdict(list)

FMT = "%m-%d-%Y %H:%M:%S"

devices = [i for i in range(1, 71)]

step = 8
matrix = []

while devices:
    row, devices = devices[:step], devices[step:]
    matrix.append(row)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Проблема", callback_data="Проблема"),
            InlineKeyboardButton("Решение", callback_data="Решение"),
            InlineKeyboardButton("Отчет", callback_data="Отчет")
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    msg = query.data

    if msg in ["Проблема", "Решение", "Отчет"]:
        keyboard = [
            [
                InlineKeyboardButton(str(d), callback_data=f"{msg} | {d}") for d in r
            ] for r in matrix
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Действие: {msg}. Выберите устройство", reply_markup=reply_markup
        )

    else:
        action, device = msg.split(" | ")

        if action in ["Проблема", "Решение"]:
            initiated.append({
                "action": action,
                "device": device,
                "time": datetime.datetime.now().strftime(FMT),
                "message": None
            })

            resp = f"Действие: {action}. Устройство: {device}. Введите описание."

        else:
            # if action == ["Проблема", "Решение"]:
            resp = f"Отчет для устройства \"{device}\":"
            reps = processed[device]
            if not reps:
                resp += "\n\nНет записей для этого устройства."
            else:
                resp += "\n\n" + "\n".join([f'<{r["time"]}> {r["action"]}: {r["message"]}' for r in reps])

        await query.edit_message_text(text=resp)


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    message = update.message

    if not initiated:
        await update.get_bot().send_message(
            chat_id=update.message.chat_id,
            text="Use /start to test this bot."
        )
        return

    record = initiated.pop()
    record["message"] = message.text
    processed[record["device"]].append(record)

    await update.get_bot().send_message(
        chat_id=update.message.chat_id,
        text=f"<{record['time']}> Принято сообщение для устройства \"{record['device']}\": \"{record['action']} :: {record['message']}\" "
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")
