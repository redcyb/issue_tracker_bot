import json
import logging
from typing import Union

import requests

from issue_tracker_bot import settings
from issue_tracker_bot.services.commands import Commands
from issue_tracker_bot.services.models import BotRequest


class TelegramSender:
    @staticmethod
    def send_telegram_message_back(chat_id, answer):
        data = {"text": answer.encode("utf8"), "chat_id": chat_id}
        url = settings.BASE_URL + "/sendMessage"

        response = requests.post(url, data).json()

        if not response["ok"]:
            raise RuntimeError(response["description"])


class TelegramService(TelegramSender):
    authorized_ids = None

    def __init__(self):
        self.load_authorized_ids()

    def load_authorized_ids(self):
        try:
            with (settings.SECRETS_PATH / "authorized_ids.json").open("r") as ff:
                self.authorized_ids = set(json.load(ff))
        except Exception:
            logging.exception("")
            self.authorized_ids = set()

    @staticmethod
    def parse_request(request_body):
        return BotRequest.model_validate(request_body)

    @staticmethod
    def get_command(request: BotRequest):
        command = request.message.text.split(" ", 1)[0]

        if command == "проблема":
            return Commands.PROBLEM

        if command == "решение":
            return Commands.SOLUTION

        if command == "отчет":
            return Commands.REPORT

    def authorize_user_id(self, user_id: Union[str, int]):
        return True
        # TODO Disable auth for short test
        return user_id in self.authorized_ids