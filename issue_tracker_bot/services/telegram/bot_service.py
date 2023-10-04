import datetime
import logging
from collections import defaultdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from issue_tracker_bot import settings
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services import GCloudService, Actions

GCloudService().enrich_app_context()
app_context = AppContext()

logger = logging.getLogger(__name__)

initiated = []
processed = defaultdict(list)


DEVICES_IN_ROW = 8


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton(Actions.PROBLEM.value, callback_data=Actions.PROBLEM.value),
            InlineKeyboardButton(Actions.SOLUTION.value, callback_data=Actions.SOLUTION.value),
            InlineKeyboardButton(Actions.REPORT.value, callback_data=Actions.REPORT.value)
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


def build_keyboard(devices_groups, action):
    keyboard = []
    for group, dev_names in devices_groups.items():
        keyboard.append([])
        while dev_names:
            batch, dev_names = (
                dev_names[:DEVICES_IN_ROW],
                dev_names[DEVICES_IN_ROW:]
            )
            keyboard.append([
                InlineKeyboardButton(
                    dev_name, callback_data=f"{action} | {dev_name}"
                ) for dev_name in batch
            ])
    return InlineKeyboardMarkup(keyboard)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    msg = query.data.strip()
    action = msg.lower()

    if action == Actions.SOLUTION.value:
        problematic_devices = filter_only_problems(app_context.devices)
        reply_markup = build_keyboard(problematic_devices, action)
        if problematic_devices:
            await query.edit_message_text(
                text=f"Дія: {msg}. Оберіть пристрій",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=f"Не знайдено жодного пристрою із відкритою проблемою",
            )

    elif action in [Actions.PROBLEM.value, Actions.REPORT.value]:
        reply_markup = build_keyboard(app_context.devices, msg)
        await query.edit_message_text(
            text=f"Дія: {msg}. Оберіть пристрій",
            reply_markup=reply_markup
        )

    else:
        action, device = msg.split(" | ")
        action = action.strip().lower()

        if action in [Actions.PROBLEM.value, Actions.SOLUTION.value]:
            initiated.append({
                "action": action,
                "device": device,
                "time": datetime.datetime.now().strftime(settings.REPORT_DT_FORMAT),
                "message": None
            })

            resp = f"Дія: \"{action}\". Устройство: \"{device}\". Введите описание."

        else:
            gcloud = GCloudService()
            report = gcloud.report_for_page(f"DEV_{device}")
            resp = f"Статус для пристрою \"{device}\":"

            if not report:
                resp = f"\n\nНема записів для пристроя \"{device}\""
            else:
                resp += f"\n{report}"

        await query.edit_message_text(text=resp)


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    txt = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.id
    bot = update.get_bot()
    user = update.message.from_user

    author = user.username
    author_str = f"@{author}"
    if not author:
        author = user.full_name
        author_str = author
    author_record = f"{author} ({user.id})"

    if not initiated:
        await update.get_bot().send_message(
            chat_id=update.message.chat_id,
            text="Use /start to test this bot."
        )
        return

    record = initiated.pop()

    gcloud = GCloudService()
    gcloud.commit_record(record["device"], record["action"], author_record, txt)

    await bot.delete_message(chat_id, message_id)
    await bot.send_message(
        chat_id=chat_id,
        text=f"{record['time']}\n"
             f"Прийнято запис від {author_str}\n"
             f"для пристроя \"{record['device']}\":\n\n"
             f"\"{record['action']} :: {txt}\" "
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")
