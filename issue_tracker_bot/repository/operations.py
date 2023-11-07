from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import Session

from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import models_db as md


@database.inject_db_session
def get_user(db: Session, obj_id: int):
    return db.query(md.User).filter(md.User.id == obj_id).first()


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_user(data_obj: dict):
    return md.User(**data_obj)


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_device(data_obj: dict):
    return md.Device(**data_obj)


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_predefined_message(data_obj: dict):
    return md.PredefinedMessage(**data_obj)


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_record(data_obj: dict):
    return md.Record(**data_obj)


@database.inject_db_session
def get_user_by_name(db: Session, name: str):
    return db.query(md.User).filter(md.User.name == name).first()


@database.inject_db_session
def get_users(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(md.User).offset(skip).limit(limit).all()


@database.inject_db_session
def get_device(
    db: Session,
    obj_id: int = None,
    name: str = None,
    group: str = None,
    serial_number: str = None,
):
    if obj_id:
        return db.query(md.Device).filter(md.Device.id == obj_id).first()
    if name and group:
        return (
            db.query(md.Device)
            .filter(md.Device.name == name, md.Device.group == group)
            .first()
        )
    if serial_number:
        return (
            db.query(md.Device).filter(md.Device.serial_number == serial_number).first()
        )


@database.inject_db_session
def get_all_devices(db: Session):
    return (
        db.query(md.Device)
        .order_by(md.Device.group.asc())
        .group_by(md.Device.group)
        .all()
    )


@database.inject_db_session
def get_records_for_device(db: Session, obj_id: int, limit: int = 10):
    return (
        db.query(md.Record)
        .where(md.Record.device_id == obj_id)
        .order_by(md.Record.created_at.desc())
        .limit(limit)
        .all()
    )


@database.inject_db_session
def get_devices_with_open_problems(db: Session):
    sub = (
        db.query(md.Record)
        .filter(md.Record.device_id == md.Device.id)
        .order_by(md.Record.created_at.desc())
        .limit(1)
        .subquery()
        .lateral()
    )

    return (
        db.query(md.Device)
        .outerjoin(sub)
        .filter_by(kind="problem")
        .options(contains_eager(md.Device.records, alias=sub))
    ).all()
