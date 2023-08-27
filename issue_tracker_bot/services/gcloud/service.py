import calendar
import logging
from datetime import datetime
from datetime import timedelta
from time import sleep
from typing import Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from issue_tracker_bot import settings
from issue_tracker_bot.services.gcloud.auth import get_credentials
from issue_tracker_bot.services.message_processing import RecordBuilder
from issue_tracker_bot.settings import configure_logging


class SheetNotFound(RuntimeError):
    ...


class GCloudService:
    drive_service = None
    sheet_service = None
    FOLDER_ID = settings.FOLDER_ID

    def __init__(self):
        self.credentials = get_credentials()
        self.drive_service = build(
            "drive", "v3", credentials=self.credentials, cache_discovery=False
        )
        self.sheet_service = build(
            "sheets", "v4", credentials=self.credentials, cache_discovery=False
        )

    def report(self):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'sheets.patch_sheet'")

        sheet_id, sheet_name = self.get_current_sheet()
        page = "Some page"
        range_ = f"'{page}'!B13:C13"

        logging.info(f"Trying to read page '{range_}' sheet '{sheet_name}'")

        sheets = self.sheet_service.spreadsheets()

        try:
            result = (
                sheets.values()
                .get(
                    spreadsheetId=sheet_id,
                    range=range_,
                    valueRenderOption="UNFORMATTED_VALUE",
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"Request to sheets.values was not successful: {exc}")

        return "\n".join(
            [f"{(str(v[0])+':').ljust(10)}{v[1]}" for v in result["values"] if v]
        )

    def list_sheets(self, prefix=settings.SHEET_PREFIX):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'drive.list_sheets'")

        files = []

        page_token = None

        while True:
            response = (
                self.drive_service.files()
                .list(
                    q=f"name contains '{prefix}' "
                    f"AND mimeType = 'application/vnd.google-apps.spreadsheet'",
                    pageToken=page_token,
                    spaces="drive",
                )
                .execute()
            )
            logging.info(f"Files found: {response.get('files', [])}")

            files += response.get("files", [])
            page_token = response.get("nextPageToken", None)

            if page_token is None:
                break

        return files

    def get_sheet_id_by_name(self, sheet_name):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'drive.list_sheets'")

        files = []

        page_token = None

        while True:
            response = (
                self.drive_service.files()
                .list(
                    q=f"name = '{sheet_name}' "
                    f"AND mimeType = 'application/vnd.google-apps.spreadsheet'",
                    pageToken=page_token,
                    spaces="drive",
                )
                .execute()
            )
            logging.info(f"Files found: {response.get('files', [])}")

            files += response.get("files", [])
            page_token = response.get("nextPageToken", None)

            if page_token is None:
                break

        if not files:
            raise SheetNotFound(
                f"No google sheets found with the name '{sheet_name}'. "
                f"Consider selecting '/clone' command"
            )

        if len(files) > 1:
            ff = [(f["name"], f["id"]) for f in files]
            logging.warning(f"More than one file with name '{sheet_name}' found: {ff}")

        return files[0]["id"]

    def load_range(self, sheet_id, range_):
        sheets = self.sheet_service.spreadsheets()

        try:
            result = (
                sheets.values()
                .get(
                    spreadsheetId=sheet_id,
                    range=range_,
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"Request to sheets.values was not successful: {exc}")
        return result

    def patch_sheet(self, sheet_id, range_, record):
        logging.debug(
            f"Trying to patch sheet '{sheet_id}' with '{record}' on page '{range_}'"
        )

        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'sheets.patch_sheet'")

        sheets = self.sheet_service.spreadsheets()

        try:
            (
                sheets.values()
                .append(
                    spreadsheetId=sheet_id,
                    range=range_,
                    body={
                        "values": [record],
                        "majorDimension": "ROWS",
                    },
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"Request to sheets.values was not successful: {exc}")

    @staticmethod
    def get_sheet_name(month, year):
        month_name = calendar.month_name[month][:3]
        return f"{settings.SHEET_PREFIX} {month_name} {year}"

    @staticmethod
    def get_previous_month_year(current_month, current_year):
        current = datetime(day=1, month=current_month, year=current_year)
        previous = current - timedelta(days=1)
        return previous.month, previous.year

    @staticmethod
    def get_current_month_year():
        today = datetime.today()
        month = today.month
        year = today.year
        return month, year

    def get_current_sheet_name(self):
        month, year = self.get_current_month_year()
        return self.get_sheet_name(month, year)

    def clone_sheet(self, sheet_id):
        target_name = self.get_current_sheet_name()
        response = (
            self.drive_service.files()
            .copy(
                fileId=sheet_id, body={"name": target_name, "parents": [self.FOLDER_ID]}
            )
            .execute()
        )
        return response

    def reset_sheet_pages(self, sheet_id):
        sheets = self.sheet_service.spreadsheets()

        pages = []

        try:
            (
                sheets.values()
                .batchClear(
                    spreadsheetId=sheet_id,
                    body={"ranges": [f"{p}!A2:F100" for p in pages]},
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"Request to sheets.values was not successful: {exc}")

    def clone_previous_sheet(self):
        month, year = self.get_current_month_year()
        month, year = self.get_previous_month_year(month, year)
        source_sheet_name = self.get_sheet_name(month, year)

        sleep(1)
        logging.info(f"Trying to retrieve sheet '{source_sheet_name}'")
        source_sheet_id = self.get_sheet_id_by_name(source_sheet_name)

        sleep(1)
        logging.info(f"Trying to clone sheet '{source_sheet_name}' ")
        clone = self.clone_sheet(source_sheet_id)
        clone_sheet_id = clone["id"]
        clone_sheet_name = clone["name"]

        sleep(1)
        logging.info(f"Trying to reset sheet '{clone_sheet_name}' ")
        self.reset_sheet_pages(clone_sheet_id)

        return source_sheet_id, source_sheet_name, clone_sheet_id, clone_sheet_name

    def delete_sheet(self, sheet_id):
        return self.drive_service.files().delete(fileId=sheet_id).execute()

    def get_current_sheet(self) -> Tuple[str, str]:
        sheet_name = self.get_current_sheet_name()
        sheet_id = self.get_sheet_id_by_name(sheet_name)
        return sheet_id, sheet_name

    def commit_clone(self) -> str:
        # First check if there is current month sheet already
        try:
            sheet_id, sheet_name = self.get_current_sheet()
        except SheetNotFound:
            ...
        else:
            return f"Current month sheet exists with name '{sheet_name}' ({sheet_id})"

        # If not sheets found - clone the old one
        try:
            (
                source_sheet_id,
                source_sheet_name,
                clone_sheet_id,
                clone_sheet_name,
            ) = self.clone_previous_sheet()
        except Exception as exc:
            logging.exception("")
            return f"Error: {exc}"

        answer = (
            f"Source sheet '{source_sheet_name}' ({source_sheet_id})"
            f"successfully cloned into '{clone_sheet_name}' ({clone_sheet_id})"
        )
        logging.info(answer)
        return answer

    def commit_record(self, message) -> str:
        try:
            sheet_id, sheet_name = self.get_current_sheet()
        except RuntimeError as exc:
            logging.exception("")
            return f"Error: {exc}"

        builder = RecordBuilder()
        builder.build(message)

        current_range_state = self.load_range(sheet_id, builder.page)
        last_record_num = len(current_range_state["values"]) + 1
        target_range = f"'{builder.page}'!A{last_record_num}:D{last_record_num}"

        try:
            self.patch_sheet(sheet_id, target_range, builder.record)
        except Exception as exc:
            logging.exception("")
            return f"Error: {exc}"

        answer = (
            f"Record was created with message '{message}' "
            f"on sheet '{sheet_name}' on page '{builder.page}'"
        )
        logging.info(answer)
        return answer
