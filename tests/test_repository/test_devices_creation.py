from pydantic_core._pydantic_core import ValidationError

from issue_tracker_bot.repository import models_pyd
from issue_tracker_bot.repository.operations import create_device
from tests.test_repository.common import DBTestCase
from tests.test_repository.factories import DeviceFactory


class DeviceModelTest(DBTestCase):
    def test_device_created_with_all_required_fields(self):
        target = DeviceFactory()
        device = create_device(models_pyd.DeviceCreate(**target))
        self.assertIsInstance(device.id, str)
        self.assertEqual(device.name, target["name"])
        self.assertEqual(device.group, target["group"])

    def test_device_not_created_without_required_fields(self):
        with self.assertRaises(ValidationError) as err:
            create_device(models_pyd.DeviceCreate())

        self.assertIn("name\n", str(err.exception))
        self.assertIn("group\n", str(err.exception))
        self.assertNotIn("created_at\n", str(err.exception))
