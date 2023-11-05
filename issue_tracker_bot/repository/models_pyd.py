from datetime import datetime
from typing import Any
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import field_validator


class UserBase(BaseModel):
    id: int
    name: Optional[str] = None
    role: Union[str, Any] = None
    records: List = []
    created_at: datetime

    @field_validator("role")
    @classmethod
    def choice_to_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return v.value


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
    kind: Union[str, Any]
    created_at: datetime

    @field_validator("kind")
    @classmethod
    def choice_to_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return v.value

    class Config:
        from_attributes = True


class Record(RecordBase):
    reporter: Optional[User] = None
    device: Optional[Device] = None

    class Config:
        from_attributes = True
