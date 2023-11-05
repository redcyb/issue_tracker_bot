from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    name: Optional[str] = None
    role: str = None
    records: List = []
    created_at: datetime


class User(UserBase):
    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    id: int
    name: str
    group: str
    serial_number: Optional[str] = None
    created_at: datetime


class Device(DeviceBase):
    class Config:
        from_attributes = True


class RecordBase(BaseModel):
    id: int
    reporter_id: int
    device_id: int
    text: str
    kind: str
    created_at: datetime


class Record(RecordBase):
    reporter: Optional[User] = None
    device: Optional[Device] = None

    class Config:
        from_attributes = True
