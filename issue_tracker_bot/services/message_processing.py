from datetime import datetime

from issue_tracker_bot import settings


class RecordBuilder:
    action = None
    message = None
    page = None
    device = None
    date = None
    record = None
    author = None

    def build(self, device: str, action: str, author: str, message: str):
        self.device = device.strip()
        self.page = f"DEV_{self.device}"
        self.action = action.strip().lower()
        self.message = message.strip()
        self.author = author.strip()
        self.date = datetime.now().strftime(settings.REPORT_DT_FORMAT)
        self.record = [None, self.date, self.author, self.action, self.message]
