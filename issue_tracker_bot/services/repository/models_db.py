from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from issue_tracker_bot.services.repository import commons
from issue_tracker_bot.services.repository import database as db


ROLES_CHOICES = [(f.value, f.value) for f in list(commons.Roles)]
KINDS_CHOICES = [(f.value, f.value) for f in list(commons.ReportKinds)]


class User(db.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(ChoiceType(ROLES_CHOICES))
    created_at = Column(DateTime, nullable=False)

    records = relationship("Record", back_populates="reporter")


class Device(db.Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    group = Column(String)
    serial_number = Column(String)
    created_at = Column(DateTime, nullable=False)

    records = relationship("Record", back_populates="device")


class Record(db.Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    kind = Column(ChoiceType(KINDS_CHOICES))
    created_at = Column(DateTime, nullable=False, index=True)

    reporter_id = Column(Integer, ForeignKey("users.id"), index=True)
    reporter = relationship("User", back_populates="records")

    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    device = relationship("Device", back_populates="records")
