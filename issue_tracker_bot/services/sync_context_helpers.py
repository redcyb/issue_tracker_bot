from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import operations as rops
from issue_tracker_bot.services import GCloudService

gcloud = GCloudService()


def sync_devices_with_gdoc():
    gdoc_devices = {gd[0]: gd for gd in gcloud.load_devices()}
    existing_devices = {ed.id: ed for ed in rops.get_devices()}
    existing_ids = set(existing_devices.keys())
    gdoc_ids = set()

    to_update = []
    to_create = []

    for did, g_device in gdoc_devices.items():
        if did in existing_devices:
            to_update.append({"id": did, "group": g_device[1], "name": g_device[2]})
        else:
            to_create.append({"id": did, "group": g_device[1], "name": g_device[2]})
        gdoc_ids.add(did)

    to_delete = list(existing_ids - gdoc_ids)

    rops.update_devices_in_batch(to_update)
    rops.create_devices_in_batch(to_create)
    rops.delete_devices_in_batch(to_delete)


def sync_predefined_messages_with_gdoc():
    rops.delete_predefined_messages_in_batch(
        [em.id for em in rops.get_predefined_messages()]
    )

    def get_objects_for_processing(kind, getter):
        _to_create = []
        _gdoc_messages = {f"{kind.value}-{md[0]}": md for md in getter()}

        for mid, g_message in _gdoc_messages.items():
            _to_create.append({"id": mid, "text": g_message[1], "kind": kind.value})

        return _to_create

    to_create_p = get_objects_for_processing(
        commons.ReportKinds.problem, gcloud.load_problems_kinds
    )
    to_create_s = get_objects_for_processing(
        commons.ReportKinds.solution, gcloud.load_solutions_kinds
    )

    rops.create_predefined_messages_in_batch(to_create_p + to_create_s)


if __name__ == "__main__":
    database.Base.metadata.create_all(bind=database.engine)
    sync_devices_with_gdoc()
    sync_predefined_messages_with_gdoc()
