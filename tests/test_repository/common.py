import os
from unittest import TestCase

from sqlalchemy.orm import close_all_sessions

from issue_tracker_bot.repository import database


class DBTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        assert os.environ["ENV"] == "test"
        database.Base.metadata.create_all(bind=database.engine)

    @classmethod
    def tearDownClass(cls):
        assert os.environ["ENV"] == "test"
        close_all_sessions()
        database.Base.metadata.drop_all(bind=database.engine)
