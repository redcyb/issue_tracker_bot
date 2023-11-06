from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import models_pyd as mp
from issue_tracker_bot.repository.operations import create_device
from issue_tracker_bot.repository.operations import create_record
from issue_tracker_bot.repository.operations import create_user
from issue_tracker_bot.repository.operations import get_devices_with_open_problems
from tests.test_repository.common import DBTestCase


class DeviceGetterModelTest(DBTestCase):
    def test_get_devices_with_open_problems(self):
        user = create_user(mp.UserCreate(id=1, name="foo", role=commons.Roles.reporter))

        # Empty devices
        create_device(mp.DeviceCreate(name="empty1", group="bar1"))
        create_device(mp.DeviceCreate(name="empty2", group="bar2"))

        device_without_open_problem1 = create_device(
            mp.DeviceCreate(name="closed1", group="bar1")
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_without_open_problem1.id,
                text="solution",
                kind=commons.ReportKinds.solution,
            )
        )

        # Devices with resolved problems
        device_without_open_problem2 = create_device(
            mp.DeviceCreate(name="closed2", group="bar2")
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_without_open_problem2.id,
                text="solution",
                kind=commons.ReportKinds.solution,
            )
        )

        # Devices with open problems
        device_with_open_problem1 = create_device(
            mp.DeviceCreate(name="open1", group="bar1")
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
                text="solution",
                kind=commons.ReportKinds.solution,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem1.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )

        device_with_open_problem2 = create_device(
            mp.DeviceCreate(name="open2", group="bar2")
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
                text="solution",
                kind=commons.ReportKinds.solution,
            )
        )
        create_record(
            mp.RecordCreate(
                reporter_id=user.id,
                device_id=device_with_open_problem2.id,
                text="problem",
                kind=commons.ReportKinds.problem,
            )
        )

        result = get_devices_with_open_problems()

        self.assertEqual(len(result), 2)
        self.assertEqual(
            set(r.id for r in result),
            {device_with_open_problem1.id, device_with_open_problem2.id},
        )