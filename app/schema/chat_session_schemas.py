import datetime
from typing import List
from pydantic import BaseModel

from app.schema.chat_message_schemas import Message


class ChatSessionBase(BaseModel):
    pass

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: int
    created_at: datetime.datetime
    messages: List[Message] = []

    class Config:
        from_attributes = True