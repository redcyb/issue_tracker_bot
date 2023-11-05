from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

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
