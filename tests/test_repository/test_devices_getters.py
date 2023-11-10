from issue_tracker_bot.repository import models_db
from issue_tracker_bot.repository import operations as ROPS
from tests.test_repository.common import cleanup_table
from tests.test_repository.common import DBTestCase
from tests.test_repository.factories import DeviceFactory
from tests.test_repository.factories import ProblemRecordFactory
from tests.test_repository.factories import ReporterFactory
from tests.test_repository.factories import SolutionRecordFactory


class DeviceGetterModelTest(DBTestCase):
    def tearDown(self):
        # Ensure tests isolation in this class
        cleanup_table(models_db.Device)

    def test_get_devices_with_open_problems(self):
        user = ROPS.create_user(ReporterFactory())

        # Empty devices
        ROPS.create_device(DeviceFactory())
        ROPS.create_device(DeviceFactory())

        device_without_open_problem1 = ROPS.create_device(DeviceFactory())
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
            )
        )
        ROPS.create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
            )
        )

        # Devices with resolved problems
        device_without_open_problem2 = ROPS.create_device(DeviceFactory())
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
            )
        )
        ROPS.create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
            )
        )

        # Devices with open problems
        device_with_open_problem1 = ROPS.create_device(DeviceFactory())
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )
        ROPS.create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
            )
        )

        device_with_open_problem2 = ROPS.create_device(DeviceFactory())
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )
        ROPS.create_record(
            SolutionRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )
        ROPS.create_record(
            ProblemRecordFactory(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
            )
        )

        result = ROPS.get_devices_with_open_problems()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            set(r.id for r in result),
            {device_with_open_problem1.id, device_with_open_problem2.id},
        )

    def test_get_device_by_id(self):
        device_id = ROPS.create_device(DeviceFactory()).id
        self.assertEqual(device_id, ROPS.get_device(obj_id=device_id).id)

    def test_get_device_by_name_and_group(self):
        name, group = "a", "b"
        ROPS.create_device(DeviceFactory(name=name, group=group))
        result = ROPS.get_device(name=name, group=group)
        self.assertEqual(name, result.name)
        self.assertEqual(group, result.group)

    def test_get_devices_grouped(self):
        for j in range(3):
            for i in range(4):
                ROPS.create_device(DeviceFactory(group=str(i)))

        result = ROPS.get_devices()

        while result:
            group, result = result[:3], result[3:]
            group = set(d.group for d in group)

            self.assertEqual(len(group), 1)
