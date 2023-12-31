from enum import Enum
from typing import Union

from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import Session
from sqlalchemy_utils.types import Choice

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import models_db as md


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_user(data_obj: dict):
    return md.User(**data_obj)


@database.pydantic_or_dict
def get_or_create_user(data_obj: dict):
    try:
        user = create_user(data_obj)
    except IntegrityError as err:
        if "already exists" in str(err):
            user = get_user(obj_id=data_obj["id"])
        else:
            raise err
    return user


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_device(data_obj: dict):
    return md.Device(**data_obj)


@database.inject_db_session
def update_devices_in_batch(db, devices):
    if not devices:
        return
    db.execute(update(md.Device), devices)
    db.commit()


@database.inject_db_session
def create_devices_in_batch(db, devices):
    if not devices:
        return
    db.execute(insert(md.Device), devices)
    db.commit()


@database.inject_db_session
def delete_devices_in_batch(db, devices):
    if not devices:
        return

    cmd = delete(md.Device).where(md.Device.id.in_(devices))
    db.execute(cmd)
    db.commit()


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_predefined_message(data_obj: dict):
    return md.PredefinedMessage(**data_obj)


@database.inject_db_session
def create_predefined_messages_in_batch(db, messages):
    if not messages:
        return
    db.execute(insert(md.PredefinedMessage), messages)
    db.commit()


@database.inject_db_session
def delete_predefined_messages_in_batch(db, messages):
    if not messages:
        return

    cmd = delete(md.PredefinedMessage).where(md.PredefinedMessage.id.in_(messages))
    db.execute(cmd)
    db.commit()


@database.inject_db_session
def update_predefined_messages_in_batch(db, messages):
    if not messages:
        return
    db.execute(update(md.PredefinedMessage), messages)
    db.commit()


@database.pydantic_or_dict
@database.inject_db_session
@database.create_commit_refresh
def create_record(data_obj: dict):
    return md.Record(**data_obj)


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
def get_devices(db: Session):
    return (
        db.query(md.Device).order_by(md.Device.group.asc(), md.Device.name.asc()).all()
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
def get_records(db: Session, limit: int = 1000):
    return db.query(md.Record).order_by(md.Record.created_at.desc()).limit(limit).all()


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


@database.inject_db_session
def get_user(db: Session, obj_id: int = None, name: str = None):
    if obj_id:
        return db.query(md.User).filter(md.User.id == obj_id).first()
    if name:
        return db.query(md.User).filter(md.User.name == name).first()


@database.inject_db_session
def get_users(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(md.User).offset(skip).limit(limit).all()


@database.inject_db_session
def get_predefined_message(db: Session, obj_id: int = None):
    return (
        db.query(md.PredefinedMessage).filter(md.PredefinedMessage.id == obj_id).first()
    )


@database.inject_db_session
def get_predefined_messages(
    db: Session,
    kind: Union[str, Choice, Enum] = None,
    skip: int = 0,
    limit: int = 10000,
):
    query = db.query(md.PredefinedMessage)

    if kind:
        if isinstance(kind, str):
            kind = Choice(kind, kind)
        elif isinstance(kind, Enum):
            kind = Choice(kind.value, kind.value)

        query = query.where(md.PredefinedMessage.kind == kind)

    return query.offset(skip).limit(limit).all()


def get_predefined_problems():
    return get_predefined_messages(commons.ReportKinds.problem)


def get_predefined_solutions():
    return get_predefined_messages(commons.ReportKinds.solution)
