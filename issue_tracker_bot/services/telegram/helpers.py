import datetime
import logging
from collections import defaultdict
from collections import namedtuple

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from issue_tracker_bot import settings
from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import models_pyd as mp
from issue_tracker_bot.repository import operations as rops
from issue_tracker_bot.services import Actions
from issue_tracker_bot.services import MenuCommandStates
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services.data_export import export_reports_to_gdoc
from issue_tracker_bot.services.sync_context_helpers import sync_devices_with_gdoc
from issue_tracker_bot.services.sync_context_helpers import (
    sync_predefined_messages_with_gdoc,
)
from issue_tracker_bot.services.telegram import app_context_helpers

# Fresh way to enrich context
app_context_helpers.enrich_app_context()

app_context = AppContext()

logger = logging.getLogger(__name__)

initiated = {}
processed = defaultdict(list)

DEVICES_IN_ROW = 4
UNGROUPED_DEVICES_LIMIT = 4
OPTIONS_IN_ROW = 2
MESSAGE_SEPARATOR = "|"
MAX_OPTION_BYTES_LEN = 41

DEFAULT_HELP_MESSAGE = (
    "Команда /start починає спілкування з ботом.\n"
    "Альтернативно можна одразу почати із доповіді\n"
    "про проблему із пристроєм командою /problem,\n"
    "про рішення проблеми із пристроєм командою /solution.\n"
    "Для отримання статусу пристрою можна використати команду /status.\n"
    "Для отримання всіх відкритих проблем - /open_problems."
)

CustomActionOption = namedtuple("CustomActionOption", ["id", "text"])
CUSTOM_ACTION_OPTION = CustomActionOption(0, "💎Свій варіант")
DONE_ACTION_OPTION = CustomActionOption(-1, "👍ЗБЕРЕГТИ 👌")

ACTION_TO_MESSAGE_KIND_MAP = {
    Actions.PROBLEM.value: commons.ReportKinds.problem.value,
    Actions.SOLUTION.value: commons.ReportKinds.solution.value,
}

MESSAGE_KIND_TO_ACTION_MAP = {
    commons.ReportKinds.problem.value: Actions.PROBLEM.value,
    commons.ReportKinds.solution.value: Actions.SOLUTION.value,
}


def build_device_full_name(device):
    return f"{device.group}-{device.name}"


def get_grouped_devices(devices):
    result = defaultdict(list)

    for device in devices:
        result[device.group].append(device)

    return result


def get_grouped_reported_devices(devices):
    result = defaultdict(list)

    for device in devices:
        if device.records:
            result[device.group].append(device)

    return result


def build_device_list_keyboard(devices_groups, action, group=None):
    keyboard = []
    cmd = MenuCommandStates.DEVICE_SELECTED_FOR_ACTION.value

    if group:
        devices_groups = {group: devices_groups[group]}

    for group, devices in devices_groups.items():
        keyboard.append([])
        while devices:
            batch, devices = (devices[:DEVICES_IN_ROW], devices[DEVICES_IN_ROW:])
            keyboard.append(
                [
                    InlineKeyboardButton(
                        build_device_full_name(device),
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


def build_group_list_keyboard(devices_groups, action):
    keyboard = []
    cmd = MenuCommandStates.DEVICE_GROUP_SELECTED_FOR_ACTION.value
    groups = list(devices_groups.keys())
    while groups:
        batch, groups = (groups[:DEVICES_IN_ROW], groups[DEVICES_IN_ROW:])
        keyboard.append(
            [
                InlineKeyboardButton(
                    group,
                    callback_data=(
                        f"{cmd}{MESSAGE_SEPARATOR}"
                        f"{action}{MESSAGE_SEPARATOR}"
                        f"{group}"
                    ),
                )
                for group in batch
            ]
        )
    return InlineKeyboardMarkup(keyboard)


def build_predefined_options_keyboard(device_id, action, selected=None):
    selected = selected or []
    keyboard = []
    cmd = MenuCommandStates.OPTION_SELECTED_FOR_ACTION.value

    # fmt: off
    options = (
        rops.get_predefined_problems()
        if action == Actions.PROBLEM.value else
        rops.get_predefined_solutions()
    )
    # fmt: on

    final_options = [
        CUSTOM_ACTION_OPTION,
        DONE_ACTION_OPTION,
    ]

    def update_keyboard_with_collection(_collection):
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✅{option.text}" if option.id in selected else option.text,
                    callback_data=(
                        f"{cmd}{MESSAGE_SEPARATOR}"
                        f"{option.id}{MESSAGE_SEPARATOR}"
                        f"{action}{MESSAGE_SEPARATOR}"
                        f"{device_id}"
                    ),
                )
                for option in _collection
            ]
        )

    while options:
        batch, options = (options[:OPTIONS_IN_ROW], options[OPTIONS_IN_ROW:])
        update_keyboard_with_collection(batch)

    update_keyboard_with_collection(final_options)
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


def prepare_group_or_device_list(grouped_devices, action, group):
    len_devices = sum(len(g) for g in grouped_devices.values())

    if len_devices <= UNGROUPED_DEVICES_LIMIT:
        reply_markup = build_device_list_keyboard(grouped_devices, action)
        return f"Дія: {action}. Оберіть пристрій", reply_markup

    if group:
        reply_markup = build_device_list_keyboard(grouped_devices, action, group)
        return f"Дія: {action}. Оберіть пристрій", reply_markup

    reply_markup = build_group_list_keyboard(grouped_devices, action)
    return f"Дія: {action}. Оберіть групу", reply_markup


async def process_initial_action_selected_button(
    msg, query=None, update=None, group=None
):
    action = msg.strip().lower()

    if action == Actions.SOLUTION.value:
        grouped_devices = get_grouped_devices(rops.get_devices_with_open_problems())

        if not grouped_devices:
            await make_response(
                text=f"Не знайдено жодного пристрою із відкритою проблемою",
                reply_markup=None,
                query=query,
                update=update,
            )
            return

        resource_message, reply_markup = prepare_group_or_device_list(
            grouped_devices, action, group
        )
        await make_response(
            text=resource_message,
            reply_markup=reply_markup,
            query=query,
            update=update,
        )
        return

    if action == Actions.PROBLEM.value:
        grouped_devices = get_grouped_devices(rops.get_devices())

        resource_message, reply_markup = prepare_group_or_device_list(
            grouped_devices, action, group
        )
        await make_response(
            text=resource_message,
            reply_markup=reply_markup,
            query=query,
            update=update,
        )
        return

    if action in Actions.STATUS.value:
        grouped_devices = get_grouped_reported_devices(rops.get_devices())

        resource_message, reply_markup = prepare_group_or_device_list(
            grouped_devices, action, group
        )
        await make_response(
            text=resource_message,
            reply_markup=reply_markup,
            query=query,
            update=update,
        )
        return

    if action == Actions.OPEN_PROBLEMS.value:
        devices = rops.get_devices_with_open_problems()

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
    device = rops.get_device(device_id)
    records = device.records

    resp = f'Статус для пристрою "{build_device_full_name(device)}":'

    if not records:
        resp = f'\n\nНема записів для пристрою "{build_device_full_name(device)}"'
    else:
        resp += "".join(
            [
                f"\n\n{r.created_at.strftime(settings.REPORT_DT_FORMAT)} {r.reporter.name}\n"
                f"{MESSAGE_KIND_TO_ACTION_MAP[r.kind].capitalize()}: {r.text}"
                for r in records
            ]
        )

    await query.edit_message_text(text=resp)


async def process_device_for_action_selected_button(msg, query):
    action, device_id = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()
    user_id = str(query.from_user.id) if query.from_user.id else None

    if action == Actions.STATUS.value:
        await process_status_action_selected(device_id, query)
        return

    initiated[user_id] = {
        "action": action,
        "device": device_id,
        "time": datetime.datetime.now().strftime(settings.REPORT_DT_FORMAT),
        "messages": [],
    }

    reply_markup = build_predefined_options_keyboard(device_id, action, selected=[])
    await query.edit_message_text(
        text=f"Оберіть повідомлення із списку", reply_markup=reply_markup
    )


async def process_group_for_action_selected_button(msg, query):
    action, group = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()

    await process_initial_action_selected_button(action, query=query, group=group)


async def make_text_to_record(txt, update):
    chat_id = update.message.chat_id
    message_id = update.message.id
    bot = update.get_bot()

    tg_user = update.message.from_user
    user_id = str(tg_user.id) if tg_user.id else None
    author_str = tg_user.username or tg_user.full_name

    user = rops.get_or_create_user(
        mp.UserCreate(id=user_id, name=author_str, role=commons.Roles.reporter)
    )

    if not initiated.get(user_id):
        await update.get_bot().send_message(
            chat_id=update.message.chat_id, text=DEFAULT_HELP_MESSAGE
        )
        return

    record_cached = initiated.pop(user_id)

    device_id, action, author = (
        record_cached["device"],
        record_cached["action"],
        user.name,
    )

    device = rops.get_device(obj_id=device_id)

    record = rops.create_record(
        mp.RecordCreate(
            reporter_id=user_id,
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
    user_id = str(tg_user.id) if tg_user.id else None
    author_str = tg_user.username or tg_user.full_name

    user = rops.get_or_create_user(
        mp.UserCreate(id=user_id, name=author_str, role=commons.Roles.reporter)
    )

    # Check if not initiated then quit
    if user_id not in initiated or not initiated[user_id]["messages"]:
        await query.edit_message_text(text=DEFAULT_HELP_MESSAGE)
        return

    # Writing record

    record = initiated.pop(user_id)

    device_id, action, messages = (
        record["device"],
        record["action"],
        record["messages"],
    )

    device = rops.get_device(obj_id=device_id)

    db_messages = {m.id: m for m in rops.get_predefined_messages() if m.id in messages}
    messages = {mid: db_messages[mid] for mid in messages}

    kind = ACTION_TO_MESSAGE_KIND_MAP[action]
    text = " +\n".join(m.text for m in messages.values())

    rops.create_record(
        mp.RecordCreate(
            reporter_id=user_id,
            device_id=device.id,
            kind=kind,
            text=text,
        )
    )

    # Responding to user
    result_text = (
        f"{record['time']}\n"
        f'Прийнято запис від "{author_str}"\n'
        f'для пристроя "{build_device_full_name(device)}":\n\n'
        f"\"{record['action'].capitalize()}: {text}\""
    )

    await query.edit_message_text(text=result_text)


async def handle_multiselect_for_action(query, update, message_id, device_id, action):
    tg_user = query.from_user
    user_id = str(tg_user.id) if tg_user.id else None

    # Check if not initiated then quit
    if user_id not in initiated:
        await query.edit_message_text(text=DEFAULT_HELP_MESSAGE)
        return

    # Adding messages to user's messages
    record = initiated[user_id]

    if message_id not in record["messages"]:
        record["messages"].append(message_id)
    else:
        record["messages"].remove(message_id)

    reply_markup = build_predefined_options_keyboard(
        device_id, action, selected=record["messages"]
    )
    await query.edit_message_text(
        text=f"Оберіть повідомлення із списку", reply_markup=reply_markup
    )


async def process_option_for_action_selected_button(msg, query, update):
    option, action, device_id = msg.split(MESSAGE_SEPARATOR)
    action = action.strip().lower()

    device = rops.get_device(obj_id=device_id)

    if option == str(DONE_ACTION_OPTION.id):
        await make_button_to_record(option, query, update)
        return

    if option == str(CUSTOM_ACTION_OPTION.id):
        resp = f'Дія: "{action}". Пристрій: "{build_device_full_name(device)}". Введіть опис:'
        await query.edit_message_text(text=resp)
        return

    await handle_multiselect_for_action(query, update, option, device_id, action)


def sync_context():
    database.Base.metadata.create_all(bind=database.engine)
    sync_devices_with_gdoc()
    sync_predefined_messages_with_gdoc()


def export_reports():
    database.Base.metadata.create_all(bind=database.engine)
    export_reports_to_gdoc()
