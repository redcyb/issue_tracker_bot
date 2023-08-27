from functools import lru_cache

from google.oauth2 import service_account

from issue_tracker_bot.settings import CREDENTIALS_PATH

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@lru_cache()
def get_credentials():
    credentials = service_account.Credentials.from_service_account_file(
        str(str(CREDENTIALS_PATH))
    )
    return credentials.with_scopes(SCOPES)
