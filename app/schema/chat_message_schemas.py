import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    session_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Stream event models
class StreamContent(BaseModel):
    type: Literal["content"]
    delta: str


class StreamToolStart(BaseModel):
    type: Literal["tool_start"]
    name: str


class StreamToolEnd(BaseModel):
    type: Literal["tool_end"]
    output: str


StreamEvent = Union[StreamContent, StreamToolStart, StreamToolEnd]
