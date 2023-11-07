from issue_tracker_bot.repository.operations import create_device
from issue_tracker_bot.repository.operations import create_record
from issue_tracker_bot.repository.operations import create_user
from issue_tracker_bot.repository.operations import get_device
from issue_tracker_bot.repository.operations import get_devices_with_open_problems
from tests.test_repository.common import DBTestCase
from tests.test_repository.factories import DeviceFactory
from tests.test_repository.factories import ProblemRecordFactory
from tests.test_repository.factories import ReporterFactory
from tests.test_repository.factories import SolutionRecordFactory


class DeviceGetterModelTest(DBTestCase):
    def test_get_devices_with_open_problems(self):
        user = create_user(ReporterFactory())

        # Empty devices
        create_device(DeviceFactory())
        create_device(DeviceFactory())

        device_without_open_problem1 = create_device(DeviceFactory())
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
            )
        )
        create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
            )
        )

        # Devices with resolved problems
        device_without_open_problem2 = create_device(DeviceFactory())
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
            )
        )
        create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
            )
        )

        # Devices with open problems
        device_with_open_problem1 = create_device(DeviceFactory())
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )
        create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )

        device_with_open_problem2 = create_device(DeviceFactory())
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )
        create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )
        create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )

        result = get_devices_with_open_problems()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            set(r.id for r in result),
            {device_with_open_problem1.id, device_with_open_problem2.id},
        )

    def test_get_device_by_id(self):
        device_id = create_device(DeviceFactory()).id
        self.assertEqual(device_id, get_device(obj_id=device_id).id)

    def test_get_device_by_name_and_group(self):
        name, group = "a", "b"
        create_device(DeviceFactory(name=name, group=group))
        result = get_device(name=name, group=group)
        self.assertEqual(name, result.name)
        self.assertEqual(group, result.group)

    def test_get_device_by_serial_number(self):
        serial_number = "a"
        create_device(DeviceFactory(serial_number=serial_number))
        result = get_device(serial_number=serial_number)
        self.assertEqual(serial_number, result.serial_number)
