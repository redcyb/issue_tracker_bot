from issue_tracker_bot.repository.operations import create_device
from issue_tracker_bot.repository.operations import create_record
from issue_tracker_bot.repository.operations import create_user
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
