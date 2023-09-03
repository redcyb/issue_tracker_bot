import logging
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from issue_tracker_bot import settings
from issue_tracker_bot.services.gcloud.auth import get_credentials
from issue_tracker_bot.services.message_processing import RecordBuilder


SHEET_ID = settings.SHEET_ID
SHEET_NAME = settings.SHEET_NAME
FOLDER_ID = settings.FOLDER_ID


class SheetNotFound(RuntimeError):
    ...


class GCloudService:
    _instance = None

    drive_service = None
    sheet_service = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(*args, **kwargs)
        return cls._instance

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

        page = "Some page"
        range_ = f"'{page}'!B13:C13"

        logging.info(f"Trying to read page '{range_}' sheet '{SHEET_NAME}'")

        sheets = self.sheet_service.spreadsheets()

        try:
            result = (
                sheets.values()
                .get(
                    spreadsheetId=SHEET_ID,
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

    def patch_sheet(self, range_, record):
        logging.debug(
            f"Trying to patch sheet '{SHEET_ID}' with '{record}' on page '{range_}'"
        )

        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'sheets.patch_sheet'")

        sheets = self.sheet_service.spreadsheets()

        try:
            (
                sheets.values()
                .append(
                    spreadsheetId=SHEET_ID,
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

    def clone_current_sheet(self):
        postfix = datetime.now().strftime(settings.GDOC_NAME_DT_FORMAT)
        target_name = f"{SHEET_NAME} - Clone - {postfix}"
        response = (
            self.drive_service.files()
            .copy(
                fileId=SHEET_ID, body={"name": target_name, "parents": [FOLDER_ID]}
            )
            .execute()
        )
        return response

    def delete_sheet(self, sheet_id):
        return self.drive_service.files().delete(fileId=sheet_id).execute()

    def commit_record(self, device, action, message) -> str:
        builder = RecordBuilder()
        builder.build(device, action, message)

        current_range_state = self.load_range(SHEET_ID, builder.page)
        last_record_num = len(current_range_state["values"]) + 1
        target_range = f"'{builder.page}'!A{last_record_num}:D{last_record_num}"

        try:
            self.patch_sheet(target_range, builder.record)
        except Exception as exc:
            logging.exception("")
            return f"Error: {exc}"

        answer = (
            f"Record was created with message '{message}' "
            f"on sheet '{SHEET_NAME}' on page '{builder.page}'"
        )
        logging.info(answer)
        return answer
