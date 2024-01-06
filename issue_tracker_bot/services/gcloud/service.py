import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from issue_tracker_bot import settings
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services.gcloud.auth import get_credentials
from issue_tracker_bot.services.message_processing import RecordBuilder

TRACKING_SHEET_ID = settings.TRACKING_SHEET_ID
SNAPSHOTS_SHEET_ID = settings.SNAPSHOTS_SHEET_ID
CONTEXT_SHEET_ID = settings.CONTEXT_SHEET_ID
FOLDER_ID = settings.FOLDER_ID

app_context = AppContext()


class SheetNotFound(RuntimeError):
    ...


class GCloudService:
    _instance = None

    drive_service = None
    sheet_service = None
    sheet_id = None

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

    def list_sheet_files(self):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'drive.list_sheets'")

        files = []

        page_token = None

        while True:
            response = (
                self.drive_service.files()
                .list(
                    q=f'"{FOLDER_ID}" in parents',
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

    def report_for_page(self, page_name):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'sheets'")

        current_range_state = self.load_range(self.sheet_id, page_name)
        if not current_range_state:
            return None

        if "values" not in current_range_state:
            return None

        values = current_range_state["values"]

        count = min(settings.REPORTS_LIMIT, len(values))

        return f"\nОстанні {count} записи:\n\n" + "\n".join(
            [f"{v[1]} {v[2]}\n{v[3].ljust(8)} : {v[4]}\n" for v in values if v]
        )

    def load_range(self, sheet_id, range_):
        sheets = self.sheet_service.spreadsheets()

        try:
            result = sheets.values().get(spreadsheetId=sheet_id, range=range_).execute()
        except HttpError as exc:
            if "Unable to parse range" in str(exc):
                return None
            raise exc

        return result

    def load_many_ranges(self, sheet_id, ranges):
        sheets = self.sheet_service.spreadsheets()

        try:
            result = (
                sheets.values()
                .batchGet(spreadsheetId=sheet_id, ranges=ranges)
                .execute()
            )
        except HttpError as exc:
            breakpoint()
            if "Unable to parse range" in str(exc):
                return None
            raise exc

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

    def delete_sheet_file(self, sheet_id):
        return self.drive_service.files().delete(fileId=sheet_id).execute()

    def create_page(self, sheet_id, page_name):
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
            sheets.batchUpdate(spreadsheetId=sheet_id, body=requests_body).execute()
        except HttpError as exc:
            raise RuntimeError(
                f"Request to sheets.batchUpdate was not successful: {exc}"
            )

    def list_all_sheets(self):
        sheet_metadata = (
            self.sheet_service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", "")
        return [
            {
                "title": sh["properties"]["title"],
            }
            for sh in sheets
        ]


class ReportTracker(GCloudService):
    sheet_id = TRACKING_SHEET_ID

    def commit_record(self, device, action, author, message) -> str:
        builder = RecordBuilder()
        builder.build(device, action, author, message)

        current_range_state = self.load_range(self.sheet_id, builder.page)

        if not current_range_state:
            self.create_page(self.sheet_id, builder.page)
            current_range_state = self.load_range(self.sheet_id, builder.page)

        try:
            last_record_num = len(current_range_state["values"]) + 1
        except KeyError:
            last_record_num = 1

        target_range = f"'{builder.page}'!A{last_record_num}:E{last_record_num}"

        try:
            self.patch_sheet(self.sheet_id, target_range, builder.record)
        except Exception as exc:
            logging.exception("")
            return f"Error: {exc}"

        self.manage_problem_in_cache(builder.action, builder.device, builder.record)
        answer = f"Record was created with message '{message}' on page '{builder.page}'"
        logging.info(answer)
        return answer


class ContextLoader(GCloudService):
    sheet_id = CONTEXT_SHEET_ID

    def load_problems_kinds(self):
        values = self.load_range(CONTEXT_SHEET_ID, "problems!A1:B1000")["values"]
        values.pop(0)  # remove header
        return values

    def load_solutions_kinds(self):
        values = self.load_range(CONTEXT_SHEET_ID, "solutions!A1:B1000")["values"]
        values.pop(0)  # remove header
        return values

    def load_devices(self):
        values = self.load_range(CONTEXT_SHEET_ID, "devices!A1:D1000")["values"]
        values.pop(0)  # remove header

        devices = [(d[0], f"{d[1]}{d[2]}", f"{int(d[3]):02d}") for d in values]

        return devices


class Snapshotter(GCloudService):
    sheet_id = SNAPSHOTS_SHEET_ID

    def export_records(self, sheet_name: str, data: list):
        ...


if __name__ == "__main__":
    from pprint import pprint

    svc = ContextLoader()
    _devices = svc.load_devices()
    _problems = svc.load_problems_kinds()
    _solutions = svc.load_solutions_kinds()

    # print(_problems)
    # print(_solutions)
    pprint(_devices)
