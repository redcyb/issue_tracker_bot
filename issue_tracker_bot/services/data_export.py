import json
from datetime import datetime

from issue_tracker_bot.repository import database
from issue_tracker_bot.repository.models_pyd import RecordExport
from issue_tracker_bot.repository.operations import get_records
from issue_tracker_bot.services import Snapshotter

gc = Snapshotter()


def export_reports_to_gdoc():
    data = get_records(limit=1000)
    data = [
        json.loads(
            RecordExport.model_validate(d).model_dump_json(
                exclude=("device_id", "reporter_id")
            )
        )
        for d in data
    ]

    header = list(data[0].keys())

    data = [header, *[list(d.values()) for d in data]]

    gc.export_records(str(datetime.now().date()), data)


if __name__ == "__main__":
    database.Base.metadata.create_all(bind=database.engine)
    export_reports_to_gdoc()
