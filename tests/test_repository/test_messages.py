from sqlalchemy.exc import IntegrityError

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_db
from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository import operations as ROPS
from tests.test_repository.common import cleanup_table
from tests.test_repository.common import DBTestCase
from tests.test_repository.factories import PredefinedMessageFactory


class PredefinedMessageModelTest(DBTestCase):
    def tearDown(self):
        # Ensure tests isolation in this class
        cleanup_table(models_db.PredefinedMessage)

    def test_message_created_with_all_required_fields(self):
        target = PredefinedMessageFactory(kind=commons.ReportKinds.problem.value)
        result = ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(**target)
        )

        self.assertIsInstance(result.id, str)
        self.assertEqual(result.text, target["text"])
        self.assertEqual(result.kind.value, commons.ReportKinds.problem.value)

    def test_message_not_created_with_non_unique_values(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                **PredefinedMessageFactory(
                    text="foo", kind=commons.ReportKinds.problem.value
                )
            )
        )

        with self.assertRaises(IntegrityError) as err:
            ROPS.create_predefined_message(
                models_pyd.PredefinedMessageCreate(
                    **PredefinedMessageFactory(
                        text="foo", kind=commons.ReportKinds.problem.value
                    )
                )
            )

    def test_get_all_predefined_messages(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(**PredefinedMessageFactory())
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(**PredefinedMessageFactory())
        )

        result = ROPS.get_predefined_messages()
        self.assertEqual(len(result), 2)

    def test_get_all_predefined_problems(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                **PredefinedMessageFactory(kind=commons.ReportKinds.problem.value)
            )
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                **PredefinedMessageFactory(kind=commons.ReportKinds.solution.value)
            )
        )

        result = ROPS.get_predefined_problems()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind.value, commons.ReportKinds.problem.value)

    def test_get_all_predefined_solutions(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                **PredefinedMessageFactory(kind=commons.ReportKinds.problem.value)
            )
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                **PredefinedMessageFactory(kind=commons.ReportKinds.solution.value)
            )
        )

        result = ROPS.get_predefined_solutions()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind.value, commons.ReportKinds.solution.value)
