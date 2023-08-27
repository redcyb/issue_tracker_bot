from datetime import datetime
from typing import Optional

from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic import field_validator


class Chat(BaseModel):
    id: int


class User(BaseModel):
    id: int
    username: Optional[str] = None


class Message(BaseModel):
    date: Optional[datetime] = None
    message_id: Optional[int] = None
    text: str
    chat: Chat
    user: User = Field(alias="from")

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str):
        return value.strip()


class BotRequest(BaseModel):
    update_id: Optional[int] = None
    message: Message
