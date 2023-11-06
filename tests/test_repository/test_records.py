from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.exc import IntegrityError

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository.operations import create_device
from issue_tracker_bot.repository.operations import create_record
from issue_tracker_bot.repository.operations import create_user
from tests.test_repository.common import DBTestCase


class RecordModelTest(DBTestCase):
    def test_record_created_with_all_required_fields(self):
        device_id = create_device(models_pyd.DeviceCreate(name="foo", group="bar")).id
        user_id = create_user(
            models_pyd.UserCreate(id=100, name="foo", role=commons.Roles.reporter)
        ).id

        record = create_record(
            models_pyd.RecordCreate(
                reporter_id=user_id,
                device_id=device_id,
                text="foo",
                kind=commons.ReportKinds.problem,
            )
        )
        self.assertIsInstance(record.id, int)
        self.assertEqual(record.device_id, device_id)
        self.assertEqual(record.reporter_id, user_id)

    def test_record_not_created_with_fake_f_keys(self):
        device_id = 1000
        user_id = 10000

        with self.assertRaises(IntegrityError) as err:
            create_record(
                models_pyd.RecordCreate(
                    reporter_id=user_id,
                    device_id=device_id,
                    text="foo",
                    kind=commons.ReportKinds.problem,
                )
            )

        self.assertIn("records_reporter_id_fkey", str(err.exception))

    def test_record_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError) as err:
            create_record(models_pyd.RecordCreate())

        self.assertIn("text\n", str(err.exception))
        self.assertIn("kind\n", str(err.exception))
        self.assertIn("reporter_id\n", str(err.exception))
        self.assertIn("device_id\n", str(err.exception))
        self.assertNotIn("created_at\n", str(err.exception))
