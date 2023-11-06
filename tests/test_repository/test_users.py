import random
from datetime import datetime

from pydantic_core._pydantic_core import ValidationError

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository.operations import create_user
from issue_tracker_bot.repository.operations import get_user
from tests.test_repository.common import DBTestCase


class UserModelTest(DBTestCase):
    def test_user_created_with_all_required_fields(self):
        uid = random.randint(1, 100000)

        create_user(
            models_pyd.UserCreate(id=uid, name="foo", role=commons.Roles.reporter)
        )

        user = get_user(uid)
        self.assertEqual(user.id, uid)
        self.assertEqual(user.role.value, commons.Roles.reporter.value)
        self.assertIsInstance(user.created_at, datetime)

    def test_user_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError) as err:
            create_user(models_pyd.UserCreate())

        self.assertIn("id\n", str(err.exception))
        self.assertIn("name\n", str(err.exception))
        self.assertIn("role\n", str(err.exception))
        self.assertNotIn("created_at\n", str(err.exception))
