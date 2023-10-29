import logging
from collections import defaultdict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from issue_tracker_bot import settings
from issue_tracker_bot.services import Actions
from issue_tracker_bot.services.context import AppContext
from issue_tracker_bot.services.gcloud.auth import get_credentials
from issue_tracker_bot.services.message_processing import RecordBuilder

TRACKING_SHEET_ID = settings.TRACKING_SHEET_ID
CONTEXT_SHEET_ID = settings.CONTEXT_SHEET_ID
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

    def enrich_app_context(self):
        self._load_devices_list()
        self._load_problems_list()
        self._load_solutions_list()
        self._load_open_problems()

    def list_sheet_files(self):
        if not self.credentials:
            raise RuntimeError("No valid credentials found for 'drive.list_sheets'")

        files = []

        page_token = None

        while True:
            response = (
                self.drive_service.files()
                .list(
                    q=f"\"{FOLDER_ID}\" in parents",
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

        current_range_state = self.load_range(TRACKING_SHEET_ID, page_name)
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
            result = (
                sheets.values()
                .get(spreadsheetId=sheet_id, range=range_)
                .execute()
            )
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
            raise RuntimeError(f"Request to sheets.batchUpdate was not successful: {exc}")

    def manage_problem_in_cache(self, action, device, problem):
        if action == Actions.PROBLEM.value:
            app_context.open_problems[device] = problem
        if action == Actions.SOLUTION.value:
            try:
                del app_context.open_problems[device]
            except KeyError:
                ...

    def commit_record(self, device, action, author, message) -> str:
        builder = RecordBuilder()
        builder.build(device, action, author, message)

        current_range_state = self.load_range(TRACKING_SHEET_ID, builder.page)

        if not current_range_state:
            self.create_page(TRACKING_SHEET_ID, builder.page)
            current_range_state = self.load_range(TRACKING_SHEET_ID, builder.page)

        try:
            last_record_num = len(current_range_state["values"]) + 1
        except KeyError:
            last_record_num = 1

        target_range = f"'{builder.page}'!A{last_record_num}:E{last_record_num}"

        try:
            self.patch_sheet(TRACKING_SHEET_ID, target_range, builder.record)
        except Exception as exc:
            logging.exception("")
            return f"Error: {exc}"

        self.manage_problem_in_cache(builder.action, builder.device, builder.record)
        answer = (
            f"Record was created with message '{message}' on page '{builder.page}'"
        )
        logging.info(answer)
        return answer

    def list_all_sheets(self):
        sheet_metadata = self.sheet_service.spreadsheets().get(spreadsheetId=TRACKING_SHEET_ID).execute()
        sheets = sheet_metadata.get("sheets", "")
        return [
            {
                "title": sh["properties"]["title"],
            } for sh in sheets
        ]

    def _load_open_problems(self):
        def _get_device(_rng: str):
            return _rng.split("!")[0].lstrip("DEV_")

        def _is_last_action_problem(_vals: list):
            if not _vals:
                # Case with empty sheet
                return False
            return _vals[-1][3].lower() == Actions.PROBLEM.value

        ranges = [f'{sh["title"]}!A:Z' for sh in self.list_all_sheets()]
        all_values = self.load_many_ranges(TRACKING_SHEET_ID, ranges)
        all_values = all_values["valueRanges"]

        device_values_map = {
            _get_device(sh["range"]): sh["values"] for sh in all_values
            if _is_last_action_problem(sh.get("values", []))
        }

        app_context.set_open_problems(device_values_map)

    def _load_problems_list(self):
        values = self.load_range(CONTEXT_SHEET_ID, "problems!A1:A1000")["values"]
        app_context.set_problems_kinds([v[0] for v in values])
        return app_context.problems_kinds

    def _load_solutions_list(self):
        values = self.load_range(CONTEXT_SHEET_ID, "solutions!A1:A1000")["values"]
        app_context.set_solutions_kinds([v[0] for v in values])
        return app_context.solutions_kinds

    def _load_devices_list(self):
        values = self.load_range(CONTEXT_SHEET_ID, "devices!A1:B1000")["values"]
        names, values = values[0], values[1:]
        groups_cnt = len(names)

        app_context.devices = defaultdict(list)

        for i in range(groups_cnt):
            group = names[i]
            app_context.devices[group] = [v[i] for v in values if v[i]]

        return app_context.devices


if __name__ == '__main__':
    from pprint import pprint

    svc = GCloudService()
    svc._load_devices_list()
    svc._load_open_problems()

    # pprint(svc.list_sheet_files())

    # svc.load_problems_list()
    # svc.load_solutions_list()

    # print(app_context.problems)
    # print(app_context.solutions)
    # pprint(app_context.devices)
