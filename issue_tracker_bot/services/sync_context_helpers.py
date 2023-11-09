from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import operations as rops
from issue_tracker_bot.services import GCloudService

gcloud = GCloudService()


def sync_devices_with_gdoc():
    gdoc_devices = {gd[0]: gd for gd in gcloud.load_devices()}
    existing_devices = {ed.id: ed for ed in rops.get_devices()}

    to_update = []
    to_create = []

    for did, g_device in gdoc_devices.items():
        if did in existing_devices:
            to_update.append({"id": did, "group": g_device[1], "name": g_device[2]})
        else:
            to_create.append({"id": did, "group": g_device[1], "name": g_device[2]})

    rops.update_devices_in_batch(to_update)
    rops.create_devices_in_batch(to_create)


if __name__ == "__main__":
    database.Base.metadata.create_all(bind=database.engine)
    sync_devices_with_gdoc()
