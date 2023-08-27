import re
from datetime import datetime

from issue_tracker_bot.services.message_to_page_mapping import get_keyword_to_page_map


class RecordBuilder:
    main_pattern_str = r"^([\w\s]+)\s+([\d\.\,]+)$"

    message = None
    text = None
    page = None
    amount = None
    date = None
    record = None

    def __init__(self):
        self.main_pattern = re.compile(self.main_pattern_str)
        self.date = str(datetime.today().date())
        self.mapping = get_keyword_to_page_map()

    def infer_page_name(self):
        groups = self.text.split(" ", 1)
        key = groups[0].lower()
        self.page = self.mapping.get(key, "Unsorted")

    def parse_message(self):
        groups = self.main_pattern.search(self.message).groups()
        self.amount = groups[-1]
        self.text = groups[-2]

    def build(self, message):
        self.message = message
        try:
            self.parse_message()
        except:
            raise RuntimeError("Bad message format. Must be like 'TYPE AMOUNT'")
        self.infer_page_name()
        self.record = [None, self.date, self.text, self.amount]
