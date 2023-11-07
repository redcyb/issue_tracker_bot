from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy_utils import ChoiceType

from issue_tracker_bot.repository import commons
from issue_tracker_bot.repository import database as db


ROLES_CHOICES = [(f.value, f.value) for f in list(commons.Roles)]
KINDS_CHOICES = [(f.value, f.value) for f in list(commons.ReportKinds)]


class User(db.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(ChoiceType(ROLES_CHOICES), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    records = relationship("Record", back_populates="reporter")


class Device(db.Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    group = Column(String, nullable=False)
    serial_number = Column(String)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    records = relationship("Record", back_populates="device")
    __table_args__ = (UniqueConstraint("name", "group", name="name_in_group"),)


class Record(db.Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    text = Column(String)
    kind = Column(ChoiceType(KINDS_CHOICES))
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    reporter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
    )
    reporter = relationship("User", back_populates="records")

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
    )
    device = relationship("Device", back_populates="records")


class PredefinedMessage(db.Base):
    __tablename__ = "predefined_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    text = Column(String, nullable=False, unique=True)
    kind = Column(ChoiceType(KINDS_CHOICES), nullable=False)
