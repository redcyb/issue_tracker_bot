from datetime import datetime
from typing import Optional

from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic.main import BaseModel


class Chat(BaseModel):
    id: int


class User(BaseModel):
    id: int
    username: Optional[str]


class Message(BaseModel):
    date: Optional[datetime]
    message_id: Optional[int]
    text: str
    chat: Chat
    user: User = Field(alias="from")

    @validator("text")
    def validate_text(cls, value: str):
        return value.strip()


class BotRequest(BaseModel):
    update_id: Optional[int]
    message: Message
