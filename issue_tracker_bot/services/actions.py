from enum import Enum


class Actions(Enum):
    PROBLEM = "проблема"
    SOLUTION = "рішення"
    STATUS = "статус"


class MenuCommandStates(Enum):
    INITIAL_ACTION_SELECTED = "ia"
    DEVICE_SELECTED_FOR_ACTION = "ds"
    OPTION_SELECTED_FOR_ACTION = "os"
