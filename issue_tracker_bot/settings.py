import logging
import os
from pathlib import Path

import dotenv

dotenv.load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

TG_READ_TIMEOUT = 30
TG_WRITE_TIMEOUT = 30

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

ENV = os.environ.get("ENV", "local")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

ROOT_PATH = Path(__file__).absolute().parent.parent
SECRETS_PATH = ROOT_PATH / "secrets"
LOG_LEVEL_STR = str(os.environ.get("LOG_LEVEL", "DEBUG"))
FOLDER_NAME = os.environ.get("FOLDER", "Home")
FOLDER_ID = os.environ["FOLDER_ID"]

if ENV == "prod":
    SECRETS_PATH = Path("/etc/secrets")
    LOG_LEVEL_STR = str(os.environ.get("LOG_LEVEL", "INFO"))

LOG_LEVEL = getattr(logging, LOG_LEVEL_STR.upper(), logging.INFO)

CREDENTIALS_PATH = SECRETS_PATH / "credentials.json"

REPORT_DT_FORMAT = "%m-%d-%Y %H:%M:%S"
GDOC_NAME_DT_FORMAT = "%m-%d-%Y---%H-%M-%S"

TRACKING_SHEET_ID = os.environ["TRACKING_SHEET_ID"]
CONTEXT_SHEET_ID = os.environ["CONTEXT_SHEET_ID"]

REPORTS_LIMIT = 10


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


configure_logging()
