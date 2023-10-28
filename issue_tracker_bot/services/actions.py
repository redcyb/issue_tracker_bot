from enum import Enum


class Actions(Enum):
    PROBLEM = "проблема"
    SOLUTION = "рішення"
    STATUS = "статус"


class MenuCommandStates(Enum):
    INITIAL_ACTION_SELECTED = "cmd_ias"
    DEVICE_SELECTED_FOR_ACTION = "cmd_dsfa"
    OPTION_SELECTED_FOR_ACTION = "cmd_osfa"
