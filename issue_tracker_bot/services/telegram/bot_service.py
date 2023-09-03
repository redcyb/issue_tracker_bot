import datetime
import logging
from collections import defaultdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from issue_tracker_bot import settings
from issue_tracker_bot.services.context import AppContext

app_context = AppContext()

logger = logging.getLogger(__name__)

initiated = []
processed = defaultdict(list)


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
        keyboard = []
        for k, v in app_context.devices.items():
            keyboard.append([])
            for row in v:
                keyboard.append([
                    InlineKeyboardButton(f"{k}{d}", callback_data=f"{msg} | {k}{d}") for d in row
                ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Действие: {msg}. Выберите устройство из групп А или В", reply_markup=reply_markup
        )

    else:
        action, device = msg.split(" | ")

        if action in ["Проблема", "Решение"]:
            initiated.append({
                "action": action,
                "device": device,
                "time": datetime.datetime.now().strftime(settings.DT_FORMAT),
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
    txt = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.id
    bot = update.get_bot()

    if not initiated:
        await update.get_bot().send_message(
            chat_id=update.message.chat_id,
            text="Use /start to test this bot."
        )
        return

    record = initiated.pop()
    record["message"] = txt
    processed[record["device"]].append(record)

    await bot.delete_message(chat_id, message_id)
    await bot.send_message(
        chat_id=chat_id,
        text=f"<{record['time']}> Принято сообщение для устройства \"{record['device']}\": \"{record['action']} :: {record['message']}\" "
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")
