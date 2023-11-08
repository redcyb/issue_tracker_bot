from typing import Union

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from issue_tracker_bot import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def inject_db_session(f):
    def wrapper(*args, **kwargs):
        """
        This injects a database Session object in function args
        """
        return f(next(get_db()), *args, **kwargs)

    return wrapper


def create_commit_refresh(f):
    def wrapper(db, *args, **kwargs):
        """
        This does all post creation actions for the object in database
        """
        db_object = f(*args, **kwargs)

        db.add(db_object)
        db.commit()
        db.refresh(db_object)

        return db_object

    return wrapper


def pydantic_or_dict(f):
    def wrapper(data_obj: Union[BaseModel, dict], *args, **kwargs):
        """
        This converts incoming data_obj to dict
        """
        data_dict = (
            data_obj.model_dump() if isinstance(data_obj, BaseModel) else data_obj
        )
        return f(data_dict, *args, **kwargs)

    return wrapper
