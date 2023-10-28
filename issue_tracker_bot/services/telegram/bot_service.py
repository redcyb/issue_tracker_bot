import datetime
import logging
from collections import defaultdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from issue_tracker_bot import settings
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services import GCloudService, Actions, MenuCommandStates

GCloudService().enrich_app_context()
app_context = AppContext()

logger = logging.getLogger(__name__)

initiated = []
processed = defaultdict(list)

DEVICES_IN_ROW = 8
OPTIONS_IN_ROW = 3
MESSAGE_SEPARATOR = " | "
CUSTOM_ACTION_OPTION = "Свій варіант"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


def filter_only_problems(devices_groups):
    result = defaultdict(list)

    for group, dev_names in devices_groups.items():
        for dev_name in dev_names:
            if dev_name in app_context.open_problems:
                result[group].append(dev_name)

    return result


def build_device_list_keyboard(devices_groups, action):
    keyboard = []
    cmd = MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value
    for group, dev_names in devices_groups.items():
        keyboard.append([])
        while dev_names:
            batch, dev_names = (
                dev_names[:DEVICES_IN_ROW],
                dev_names[DEVICES_IN_ROW:]
            )
            keyboard.append([
                InlineKeyboardButton(
                    dev_name, callback_data=f"{cmd} | {action} | {dev_name}"
                ) for dev_name in batch
            ])
    return InlineKeyboardMarkup(keyboard)


def build_predefined_options_keyboard(dev_name, action):
    keyboard = []
    cmd = MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value

    # fmt: off
    options = (
        app_context.problems_kinds
        if action == Actions.PROBLEM.value else
        app_context.solutions_kinds
    )
    # fmt: on

    options += [CUSTOM_ACTION_OPTION]

    while options:
        batch, options = (
            options[:OPTIONS_IN_ROW],
            options[OPTIONS_IN_ROW:]
        )
        keyboard.append([
            InlineKeyboardButton(
                option, callback_data=f"{cmd} | {option} | {action} | {dev_name}"
            ) for option in batch
        ])
    return InlineKeyboardMarkup(keyboard)


async def handle_initial_action_selected_button(msg, query):
    action = msg.strip().lower()

    if action == Actions.SOLUTION.value:
        problematic_devices = filter_only_problems(app_context.devices)
        reply_markup = build_device_list_keyboard(problematic_devices, action)
        if problematic_devices:
            await query.edit_message_text(
                text=f"Дія: {msg}. Оберіть пристрій",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=f"Не знайдено жодного пристрою із відкритою проблемою",
            )
        return

    if action in [Actions.PROBLEM.value, Actions.STATUS.value]:
        reply_markup = build_device_list_keyboard(app_context.devices, msg)
        await query.edit_message_text(
            text=f"Дія: {msg}. Оберіть пристрій",
            reply_markup=reply_markup
        )
        return

    raise Exception(f"Unexpected initial action: '{msg}'")


async def handle_status_action_selected(device, query):
    gcloud = GCloudService()
    report = gcloud.report_for_page(f"DEV_{device}")
    resp = f"Статус для пристрою \"{device}\":"

    if not report:
        resp = f"\n\nНема записів для пристроя \"{device}\""
    else:
        resp += f"\n{report}"

    await query.edit_message_text(text=resp)


async def handle_device_for_action_selected_button(msg, query):
    action, device = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()

    if action == Actions.STATUS.value:
        await handle_status_action_selected(device, query)
        return

    initiated.append({
        "action": action,
        "device": device,
        "time": datetime.datetime.now().strftime(settings.REPORT_DT_FORMAT),
        "message": None
    })

    reply_markup = build_predefined_options_keyboard(device, action)
    await query.edit_message_text(
        text=f"Оберіть повідомлення із списку", reply_markup=reply_markup
    )


async def make_text_to_record(txt, update):
    chat_id = update.message.chat_id
    message_id = update.message.id
    bot = update.get_bot()
    user = update.message.from_user

    author_str = f"'{user.username or user.full_name}'"

    if not initiated:
        await update.get_bot().send_message(
            chat_id=update.message.chat_id,
            text="Use /start to test this bot."
        )
        return

    record = initiated.pop()

    gcloud = GCloudService()
    gcloud.commit_record(record["device"], record["action"], author_str, txt)

    await bot.delete_message(chat_id, message_id)
    await bot.send_message(
        chat_id=chat_id,
        text=f"{record['time']}\n"
             f"Прийнято запис від {author_str}\n"
             f"для пристроя \"{record['device']}\":\n\n"
             f"\"{record['action']} :: {txt}\" "
    )


async def make_button_to_record(txt, query, update):
    user = query.from_user
    author_str = f"'{user.username or user.full_name}'"

    # Check if not initiated then quit

    if not initiated:
        await query.edit_message_text(text="Use /start to test this bot.")
        return

    # Writing record

    record = initiated.pop()
    gcloud = GCloudService()
    gcloud.commit_record(record["device"], record["action"], author_str, txt)

    # Responding to user

    result_text = (
        f"{record['time']}\n"
        f"Прийнято запис від {author_str}\n"
        f"для пристроя \"{record['device']}\":\n\n"
        f"\"{record['action']} :: {txt}\" "
    )

    await query.edit_message_text(text=result_text)


async def handle_option_for_action_selected_button(msg, query, update):
    option, action, device = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()

    if option == CUSTOM_ACTION_OPTION:
        resp = f"Дія: \"{action}\". Пристрій: \"{device}\". Введіть опис:"
        await query.edit_message_text(text=resp)
        return

    await make_button_to_record(option, query, update)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    initial_msg = query.data.strip()
    cmd, msg = initial_msg.split(MESSAGE_SEPARATOR, 1)

    if cmd == MenuCommandStates.INITIAL_ACTION_SELECTED.value:
        await handle_initial_action_selected_button(msg, query)
        return

    if cmd == MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value:
        await handle_device_for_action_selected_button(msg, query)
        return

    if cmd == MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value:
        await handle_option_for_action_selected_button(msg, query, update)
        return

    raise Exception(f"Unexpected command: '{cmd}'")


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    txt = update.message.text
    await make_text_to_record(txt, update)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")
