from typing import List, Type

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.chat_models import Message


class ChatMessageRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self._session = db

    def get_by_session_id(self, session_id: int, skip: int = 0, limit: int = 100) -> List[Type[Message]]:
        return self._session.query(Message).filter_by(session_id = session_id).offset(skip).limit(limit).all()

    def create(self, message: Message) -> Message:
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message

    def update(self, message: Message) -> Message:
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message
