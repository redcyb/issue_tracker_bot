import logging
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from issue_tracker_bot import settings
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services.gcloud.auth import get_credentials
from issue_tracker_bot.services.message_processing import RecordBuilder

SHEET_ID = settings.SHEET_ID
SHEET_NAME = settings.SHEET_NAME
FOLDER_ID = settings.FOLDER_ID

app_context = AppContext()


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

    def report_for_page(self, page_name):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'sheets'")

        current_range_state = self.load_range(page_name)
        if not current_range_state:
            return None

        if "values" not in current_range_state:
            return None

        values = current_range_state["values"]

        count = min(settings.REPORTS_LIMIT, len(values))

        return f"\nПоследние {count} запис(ь/и/ей):\n\n" + "\n".join(
            [f"{v[1]} : {v[2].ljust(8)} : {v[3]}" for v in values if v]
        )

    def list_sheet_files(self, prefix=settings.SHEET_PREFIX):
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

    def load_range(self, range_):
        sheets = self.sheet_service.spreadsheets()

        try:
            result = (
                sheets.values()
                .get(spreadsheetId=SHEET_ID, range=range_)
                .execute()
            )
        except HttpError as exc:
            if "Unable to parse range" in str(exc):
                return None
            raise exc

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

    def clone_current_sheet_file(self):
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

    def delete_sheet_file(self, sheet_id):
        return self.drive_service.files().delete(fileId=sheet_id).execute()

    def create_page(self, page_name):
        sheets = self.sheet_service.spreadsheets()

        requests_body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": page_name,
                        }
                    }
                }
            ]
        }

        try:
            sheets.batchUpdate(spreadsheetId=SHEET_ID, body=requests_body).execute()
        except HttpError as exc:
            raise RuntimeError(f"Request to sheets.batchUpdate was not successful: {exc}")

    def commit_record(self, device, action, message) -> str:
        builder = RecordBuilder()
        builder.build(device, action, message)

        current_range_state = self.load_range(builder.page)

        if not current_range_state:
            self.create_page(builder.page)
            current_range_state = self.load_range(builder.page)

        try:
            last_record_num = len(current_range_state["values"]) + 1
        except KeyError:
            last_record_num = 1

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
