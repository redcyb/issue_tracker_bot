from collections import defaultdict

from issue_tracker_bot.repository import operations as ROPS
from issue_tracker_bot.services.context import AppContext

app_context = AppContext()


def load_devices_list():
    devices = ROPS.get_devices()
    result = defaultdict(list)

    for d in devices:
        result[d.group].append(d)

    app_context.set_devices(result)


def load_problems_list():
    app_context.set_problems_kinds([p.text for p in ROPS.get_predefined_problems()])


def load_solutions_list():
    app_context.set_solutions_kinds([p.text for p in ROPS.get_predefined_solutions()])


def load_open_problems():
    ...
