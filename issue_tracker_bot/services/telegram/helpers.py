import datetime
import logging
from collections import defaultdict
from collections import namedtuple

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from issue_tracker_bot import settings
from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_pyd as mp
from issue_tracker_bot.repository import operations as ROPS
from issue_tracker_bot.services import Actions
from issue_tracker_bot.services import MenuCommandStates
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services.message_processing import RecordBuilder
from issue_tracker_bot.services.telegram import app_context_helpers

# Fresh way to enrich context
app_context_helpers.enrich_app_context()

app_context = AppContext()

logger = logging.getLogger(__name__)

initiated = {}
processed = defaultdict(list)

DEVICES_IN_ROW = 8
OPTIONS_IN_ROW = 2
MESSAGE_SEPARATOR = "|"
MAX_OPTION_BYTES_LEN = 41

DEFAULT_HELP_MESSAGE = (
    "Команда /start починає спілкування з ботом.\n"
    "Альтернативно можна одразу почати із доповіді\n"
    "про проблему із пристроєм командою /problem,\n"
    "про рішення проблеми із пристроєм командою /solution.\n"
    "Для отримання статусу пристрою можна використати команду /status."
)

CustomActionOption = namedtuple("CustomActionOption", ["id", "text"])
CUSTOM_ACTION_OPTION = CustomActionOption(0, "Свій варіант")

ACTION_TO_MESSAGE_KIND_MAP = {
    Actions.PROBLEM.value: commons.ReportKinds.problem.value,
    Actions.SOLUTION.value: commons.ReportKinds.solution.value,
}

MESSAGE_KIND_TO_ACTION_MAP = {
    commons.ReportKinds.problem.value: Actions.PROBLEM.value,
    commons.ReportKinds.solution.value: Actions.SOLUTION.value,
}


def build_device_full_name(device):
    return f"{device.name} (гр. {device.group})"


def get_grouped_devices(devices):
    result = defaultdict(list)

    for device in devices:
        result[device.group].append(device)

    return result


def build_device_list_keyboard(devices_groups, action):
    keyboard = []
    cmd = MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value
    for group, devices in devices_groups.items():
        keyboard.append([])
        while devices:
            batch, devices = (devices[:DEVICES_IN_ROW], devices[DEVICES_IN_ROW:])
            keyboard.append(
                [
                    InlineKeyboardButton(
                        device.name,
                        callback_data=(
                            f"{cmd}{MESSAGE_SEPARATOR}"
                            f"{action}{MESSAGE_SEPARATOR}"
                            f"{device.id}"
                        ),
                    )
                    for device in batch
                ]
            )
    return InlineKeyboardMarkup(keyboard)


def build_predefined_options_keyboard(device_id, action):
    keyboard = []
    cmd = MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value

    # fmt: off
    options = (
        ROPS.get_predefined_problems()
        if action == Actions.PROBLEM.value else
        ROPS.get_predefined_solutions()
    )
    # fmt: on

    options += [CUSTOM_ACTION_OPTION]

    while options:
        batch, options = (options[:OPTIONS_IN_ROW], options[OPTIONS_IN_ROW:])
        keyboard.append(
            [
                InlineKeyboardButton(
                    option.text,
                    callback_data=(
                        f"{cmd}{MESSAGE_SEPARATOR}"
                        f"{option.id}{MESSAGE_SEPARATOR}"
                        f"{action}{MESSAGE_SEPARATOR}"
                        f"{device_id}"
                    ),
                )
                for option in batch
            ]
        )
    return InlineKeyboardMarkup(keyboard)


async def make_response(text, reply_markup, query=None, update=None):
    kwargs = {"text": text}

    if reply_markup:
        kwargs["reply_markup"] = reply_markup

    if query:
        await query.edit_message_text(**kwargs)
        return

    if update:
        await update.message.reply_text(**kwargs)
        return

    raise Exception("Either query or update must be provided.")


async def process_initial_action_selected_button(msg, query=None, update=None):
    action = msg.strip().lower()

    if action == Actions.SOLUTION.value:
        problematic_devices = get_grouped_devices(ROPS.get_devices_with_open_problems())
        reply_markup = build_device_list_keyboard(problematic_devices, action)
        if problematic_devices:
            await make_response(
                text=f"Дія: {msg}. Оберіть пристрій",
                reply_markup=reply_markup,
                query=query,
                update=update,
            )
        else:
            await make_response(
                text=f"Не знайдено жодного пристрою із відкритою проблемою",
                reply_markup=None,
                query=query,
                update=update,
            )
        return

    if action in [Actions.PROBLEM.value, Actions.STATUS.value]:
        grouped_devices = get_grouped_devices(ROPS.get_devices())
        reply_markup = build_device_list_keyboard(grouped_devices, msg)
        await make_response(
            text=f"Дія: {msg}. Оберіть пристрій",
            reply_markup=reply_markup,
            query=query,
            update=update,
        )
        return

    if action == Actions.OPEN_PROBLEMS.value:
        devices = ROPS.get_devices_with_open_problems()

        result = f"\nВсього відкрито проблем {len(devices)}:\n"
        result += "\n".join(
            f"\n{build_device_full_name(d)}:"
            f"\n{d.records[-1].created_at.strftime(settings.REPORT_DT_FORMAT)}"
            f"\n{d.records[-1].text}"
            for d in devices
        )

        await make_response(
            text=result,
            reply_markup=None,
            query=query,
            update=update,
        )
        return

    raise Exception(f"Unexpected initial action: '{msg}'")


async def process_status_action_selected(device_id, query):
    # gcloud = GCloudService()
    # report = gcloud.report_for_page(f"DEV_{device}")

    device = ROPS.get_device(device_id)
    records = device.records

    resp = f'Статус для пристрою "{build_device_full_name(device)}":'

    if not records:
        resp = f'\n\nНема записів для пристрою "{build_device_full_name(device)}"'
    else:
        # 10-29-2023 12:55:48 redcyb'
        # проблема : Проблема 1 Use of language

        resp += "".join(
            [
                f"\n\n{r.created_at.strftime(settings.REPORT_DT_FORMAT)} {r.reporter.name}\n{r.kind} : {r.text}"
                for r in records
            ]
        )

    await query.edit_message_text(text=resp)


async def process_device_for_action_selected_button(msg, query):
    action, device_id = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()
    user_id = query.from_user.id

    if action == Actions.STATUS.value:
        await process_status_action_selected(device_id, query)
        return

    initiated[user_id] = {
        "action": action,
        "device": device_id,
        "time": datetime.datetime.now().strftime(settings.REPORT_DT_FORMAT),
        "message": None,
    }

    reply_markup = build_predefined_options_keyboard(device_id, action)
    await query.edit_message_text(
        text=f"Оберіть повідомлення із списку", reply_markup=reply_markup
    )


async def make_text_to_record(txt, update):
    chat_id = update.message.chat_id
    message_id = update.message.id
    bot = update.get_bot()

    tg_user = update.message.from_user
    user_id = tg_user.id
    author_str = tg_user.username or tg_user.full_name

    user = ROPS.get_or_create_user(
        mp.UserCreate(id=user_id, name=author_str, role=commons.Roles.reporter)
    )

    if not initiated.get(user_id):
        await update.get_bot().send_message(
            chat_id=update.message.chat_id, text=DEFAULT_HELP_MESSAGE
        )
        return

    record_cached = initiated.pop(user.id)

    device_id, action, author = (
        record_cached["device"],
        record_cached["action"],
        user.name,
    )

    device = ROPS.get_device(obj_id=device_id)

    record = ROPS.create_record(
        mp.RecordCreate(
            reporter_id=user.id,
            device_id=device.id,
            kind=ACTION_TO_MESSAGE_KIND_MAP[action],
            text=txt,
        )
    )

    await bot.delete_message(chat_id, message_id)
    await bot.send_message(
        chat_id=chat_id,
        text=f"{record.created_at.strftime(settings.REPORT_DT_FORMAT)}\n"
        f"Прийнято запис від '{user.name}'\n"
        f'для пристроя "{build_device_full_name(device)}":\n\n'
        f'"{action} :: {record.text}" ',
    )


async def make_button_to_record(message_id, query, update):
    tg_user = query.from_user
    user_id = tg_user.id
    author_str = tg_user.username or tg_user.full_name

    user = ROPS.get_or_create_user(
        mp.UserCreate(id=user_id, name=author_str, role=commons.Roles.reporter)
    )

    # Check if not initiated then quit
    if not initiated:
        await query.edit_message_text(text=DEFAULT_HELP_MESSAGE)
        return

    # Writing record

    record = initiated.pop(user.id)

    device_id, action, author, message_id = (
        record["device"],
        record["action"],
        author_str,
        message_id,
    )

    device = ROPS.get_device(obj_id=device_id)
    message = ROPS.get_predefined_message(obj_id=message_id)

    ROPS.create_record(
        mp.RecordCreate(
            reporter_id=user.id,
            device_id=device.id,
            kind=message.kind,
            text=message.text,
        )
    )

    builder = RecordBuilder()
    builder.build(device.name, action, author, message.text)

    # Responding to user

    result_text = (
        f"{record['time']}\n"
        f'Прийнято запис від "{author_str}"\n'
        f'для пристроя "{build_device_full_name(device)}":\n\n'
        f"\"{record['action']} :: {message.text}\" "
    )

    await query.edit_message_text(text=result_text)


async def process_option_for_action_selected_button(msg, query, update):
    option, action, device_id = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()

    device = ROPS.get_device(obj_id=device_id)

    if option == str(CUSTOM_ACTION_OPTION.id):
        resp = f'Дія: "{action}". Пристрій: "{build_device_full_name(device)}". Введіть опис:'
        await query.edit_message_text(text=resp)
        return

    await make_button_to_record(option, query, update)
