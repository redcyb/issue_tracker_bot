from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import Session

from issue_tracker_bot.repository import database
from issue_tracker_bot.repository import models_db as md
from issue_tracker_bot.repository.database import pydantic_or_dict


@database.inject_db_session
def get_user(db: Session, obj_id: int):
    return db.query(md.User).filter(md.User.id == obj_id).first()


@pydantic_or_dict
@database.inject_db_session
def create_user(db: Session, data_obj: dict):
    db_object = md.User(**data_obj)

    db.add(db_object)
    db.commit()
    db.refresh(db_object)

    return db_object


@pydantic_or_dict
@database.inject_db_session
def create_device(db: Session, data_obj: dict):
    db_object = md.Device(**data_obj)

    db.add(db_object)
    db.commit()
    db.refresh(db_object)

    return db_object


@pydantic_or_dict
@database.inject_db_session
def create_record(db: Session, data_obj: dict):
    db_object = md.Record(**data_obj)

    db.add(db_object)
    db.commit()
    db.refresh(db_object)

    return db_object


@database.inject_db_session
def get_user_by_name(db: Session, name: str):
    return db.query(md.User).filter(md.User.name == name).first()


@database.inject_db_session
def get_users(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(md.User).offset(skip).limit(limit).all()


@database.inject_db_session
def get_device(db: Session, obj_id: int):
    return db.query(md.Device).filter(md.Device.id == obj_id).first()


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
