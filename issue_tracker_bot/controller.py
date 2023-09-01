import logging
from time import sleep

from issue_tracker_bot.services import Commands
# from issue_tracker_bot.services import GCloudService
from issue_tracker_bot.services import TelegramService


class Controller:
    gcloud_service = None
    telegram_service = None

    def __init__(self):
        self.gcloud_service = None  # GCloudService()
        self.telegram_service = TelegramService()

    def process(self, request_body: dict):
        sleep(1)

        request = self.telegram_service.parse_request(request_body)
        chat_id = request.message.chat.id
        user_id = request.message.user.id

        logging.info(
            f"Handling message '{request.message.text}' "
            f"for user: {request.message.user}"
        )

        if not self.telegram_service.authorize_user_id(user_id):
            self.telegram_service.send_telegram_message_back(chat_id, "No Action")
            return

        # TODO This is only for initial testing without domain
        logging.info(f"chat_id: '{chat_id}'")
        self.telegram_service.send_telegram_message_back(chat_id, request.model_dump_json())

        command = self.telegram_service.get_command(request)
        chat_id = request.message.chat.id

        if command == Commands.REPORT:
            result = "последние обновления\n1\n2\n3"
            self.telegram_service.send_telegram_message_back(chat_id, result)
            # try:
            #     result = self.gcloud_service.report()
            # except RuntimeError as exc:
            #     logging.exception("")
            #     result = f"Error: {exc}"
            # self.telegram_service.send_telegram_message_back(chat_id, result)
            return

        if command == Commands.PROBLEM:
            txt = request.message.text
            parsed = txt.split(" ", 2)
            c, d, _ = parsed
            result = f"принял сообщение о проблеме с устройством: {d}"

            self.telegram_service.send_telegram_message_back(chat_id, result)
            # result = self.gcloud_service.commit_record(request.message.text)
            # self.telegram_service.send_telegram_message_back(chat_id, result)
            # sleep(1)
            # result = self.gcloud_service.report()
            # self.telegram_service.send_telegram_message_back(chat_id, result)
            return

        if command == Commands.SOLUTION:
            txt = request.message.text
            parsed = txt.split(" ", 2)
            c, d, _ = parsed
            result = f"принял сообщение о починке устройства: {d}"

            self.telegram_service.send_telegram_message_back(chat_id, result)
            # result = self.gcloud_service.commit_record(request.message.text)
            # self.telegram_service.send_telegram_message_back(chat_id, result)
            # sleep(1)
            # result = self.gcloud_service.report()
            # self.telegram_service.send_telegram_message_back(chat_id, result)
            return
