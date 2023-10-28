from telegram import Update
from telegram.ext import ContextTypes

from issue_tracker_bot.services.telegram.helpers import *

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    cmd = MenuCommandStates.INITIAL_ACTION_SELECTED.value

    keyboard = [
        [
            InlineKeyboardButton(Actions.PROBLEM.value, callback_data=f"{cmd} | {Actions.PROBLEM.value}"),
            InlineKeyboardButton(Actions.SOLUTION.value, callback_data=f"{cmd} | {Actions.SOLUTION.value}"),
            InlineKeyboardButton(Actions.STATUS.value, callback_data=f"{cmd} | {Actions.STATUS.value}")
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Оберіть Дію:", reply_markup=reply_markup)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    initial_msg = query.data.strip()
    cmd, msg = initial_msg.split(MESSAGE_SEPARATOR, 1)

    if cmd == MenuCommandStates.INITIAL_ACTION_SELECTED.value:
        await process_initial_action_selected_button(msg, query)
        return

    if cmd == MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value:
        await process_device_for_action_selected_button(msg, query)
        return

    if cmd == MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value:
        await process_option_for_action_selected_button(msg, query, update)
        return

    raise Exception(f"Unexpected command: '{cmd}'")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    txt = update.message.text
    await make_text_to_record(txt, update)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")
