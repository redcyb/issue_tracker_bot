import logging

from telegram import Update
from telegram.ext import ContextTypes

from issue_tracker_bot.services.telegram import helpers as H

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    cmd = H.MenuCommandStates.INITIAL_ACTION_SELECTED.value

    keyboard = [
        [
            H.InlineKeyboardButton(
                H.Actions.PROBLEM.value,
                callback_data=f"{cmd}{H.MESSAGE_SEPARATOR}{H.Actions.PROBLEM.value}",
            ),
            H.InlineKeyboardButton(
                H.Actions.SOLUTION.value,
                callback_data=f"{cmd}{H.MESSAGE_SEPARATOR}{H.Actions.SOLUTION.value}",
            ),
            H.InlineKeyboardButton(
                H.Actions.STATUS.value,
                callback_data=f"{cmd}{H.MESSAGE_SEPARATOR}{H.Actions.STATUS.value}",
            ),
        ],
        [
            H.InlineKeyboardButton(
                H.Actions.OPEN_PROBLEMS.value,
                callback_data=f"{cmd}{H.MESSAGE_SEPARATOR}{H.Actions.OPEN_PROBLEMS.value}",
            )
        ],
    ]

    reply_markup = H.InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Оберіть Дію:", reply_markup=reply_markup)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    initial_msg = query.data.strip()
    cmd, msg = initial_msg.split(H.MESSAGE_SEPARATOR, 1)

    if cmd == H.MenuCommandStates.INITIAL_ACTION_SELECTED.value:
        await H.process_initial_action_selected_button(msg, query=query)
        return

    if cmd == H.MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value:
        await H.process_device_for_action_selected_button(msg, query=query)
        return

    if cmd == H.MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value:
        await H.process_option_for_action_selected_button(
            msg, query=query, update=update
        )
        return

    raise Exception(f"Unexpected command: '{cmd}'")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    txt = update.message.text
    await H.make_text_to_record(txt, update)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(H.DEFAULT_HELP_MESSAGE)


async def handle_init_problem_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await H.process_initial_action_selected_button(
        H.Actions.PROBLEM.value, update=update
    )


async def handle_init_solution_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await H.process_initial_action_selected_button(
        H.Actions.SOLUTION.value, update=update
    )


async def handle_init_status_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await H.process_initial_action_selected_button(
        H.Actions.STATUS.value, update=update
    )


async def handle_open_problems_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await H.process_initial_action_selected_button(
        H.Actions.OPEN_PROBLEMS.value, update=update
    )


async def handle_sync_context_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        H.sync_context()
    except Exception:
        logger.exception("")
        await update.message.reply_text(f"Error during handling request 'sync_context'")
    else:
        await update.message.reply_text(f"Контекст успішно синхронізовано")
