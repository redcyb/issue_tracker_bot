from sqlalchemy.orm import Session

from issue_tracker_bot.services.repository import database
from issue_tracker_bot.services.repository import models_db as md, models_pyd as mp


@database.inject_db_session
def get_user(db: Session, user_id: int):
    return db.query(md.User).filter(md.User.id == user_id).first()


@database.inject_db_session
def create_user(db: Session, user: mp.User):
    db_object = md.User(**user.model_dump())

    db.add(db_object)
    db.commit()
    db.refresh(db_object)

    return db_object


@database.inject_db_session
def create_device(db: Session, device: mp.Device):
    db_object = md.Device(**device.model_dump())

    db.add(db_object)
    db.commit()
    db.refresh(db_object)

    return db_object


@database.inject_db_session
def create_record(db: Session, record: mp.Record):
    db_object = md.Record(**record.model_dump())

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
