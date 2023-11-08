from datetime import datetime
from enum import Enum
from typing import Any
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator
from sqlalchemy_utils.types import Choice


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    name: str
    role: Union[str, Choice, Enum]
    records: List = []
    created_at: datetime

    @field_validator("role")
    @classmethod
    def choice_to_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return v.value


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    created_at: Optional[datetime] = None


class DeviceBase(BaseModel):
    id: Optional[int] = None
    name: str
    group: str
    serial_number: Optional[str] = None
    created_at: datetime


class Device(DeviceBase):
    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: Optional[datetime] = None


class RecordBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: Optional[int] = None
    reporter_id: int
    device_id: int
    text: str
    kind: Union[str, Choice, Enum]
    created_at: datetime

    @field_validator("kind")
    @classmethod
    def choice_to_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return v.value


class RecordLight(RecordBase):
    model_config = ConfigDict(from_attributes=True)


class RecordCreate(RecordBase):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    created_at: Optional[datetime] = None


class Record(RecordBase):
    model_config = ConfigDict(from_attributes=True)
    reporter: Optional[User] = None
    device: Optional[Device] = None


class PredefinedMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    text: str
    kind: Union[str, Choice, Enum]

    @field_validator("kind")
    @classmethod
    def choice_to_str(cls, v: Any) -> str:
        if isinstance(v, str):
            return v
        return v.value


class PredefinedMessageCreate(PredefinedMessage):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
