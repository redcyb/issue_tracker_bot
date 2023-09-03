from datetime import datetime

from issue_tracker_bot import settings


class RecordBuilder:
    action = None
    message = None
    page = None
    device = None
    date = None
    record = None

    def build(self, device: str, action: str, message: str):
        self.page = device.strip()
        self.action = action.strip()
        self.message = message.strip()
        self.date = datetime.now().strftime(settings.REPORT_DT_FORMAT)
        self.record = [None, self.date, self.action, self.message]
