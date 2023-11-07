from sqlalchemy.exc import IntegrityError

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import models_db
from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository import operations as ROPS
from tests.test_repository.common import DBTestCase


@database.inject_db_session
def cleanup_table(db, model):
    try:
        num_rows_deleted = db.query(model).delete()
        db.commit()
    except:
        db.rollback()
    else:
        return num_rows_deleted


class PredefinedMessageModelTest(DBTestCase):
    def tearDown(self):
        # Ensure tests isolation in this class
        cleanup_table(models_db.PredefinedMessage)

    def test_message_created_with_all_required_fields(self):
        result = ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="foo", kind=commons.ReportKinds.problem
            )
        )

        self.assertIsInstance(result.id, int)
        self.assertEqual(result.text, "foo")
        self.assertEqual(result.kind.value, commons.ReportKinds.problem.value)

    def test_message_not_created_with_non_unique_values(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="foo", kind=commons.ReportKinds.problem
            )
        )

        with self.assertRaises(IntegrityError) as err:
            ROPS.create_predefined_message(
                models_pyd.PredefinedMessageCreate(
                    text="foo", kind=commons.ReportKinds.problem
                )
            )

    def test_get_all_predefined_messages(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="p1", kind=commons.ReportKinds.problem
            )
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="s1", kind=commons.ReportKinds.solution
            )
        )

        result = ROPS.get_predefined_messages()
        self.assertEqual(len(result), 2)

    def test_get_all_predefined_problems(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="p1", kind=commons.ReportKinds.problem
            )
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="s1", kind=commons.ReportKinds.solution
            )
        )

        result = ROPS.get_predefined_problems()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind.value, commons.ReportKinds.problem.value)

    def test_get_all_predefined_solutions(self):
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="p1", kind=commons.ReportKinds.problem
            )
        )
        ROPS.create_predefined_message(
            models_pyd.PredefinedMessageCreate(
                text="s1", kind=commons.ReportKinds.solution
            )
        )

        result = ROPS.get_predefined_solutions()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind.value, commons.ReportKinds.solution.value)
