from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.exc import IntegrityError

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository.operations import create_predefined_message
from tests.test_repository.common import DBTestCase


class PredefinedMessageModelTest(DBTestCase):
    def test_message_created_with_all_required_fields(self):
        result = create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="foo", kind=commons.ReportKinds.problem
            )
        )

        self.assertIsInstance(result.id, int)
        self.assertEqual(result.text, "foo")
        self.assertEqual(result.kind.value, commons.ReportKinds.problem.value)
