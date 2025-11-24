from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.model.chat_models import ChatSession


class ChatSessionRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self._session = db

    def get(self, skip: int = 0, limit: int = 100) -> list[type[ChatSession]]:
        return self._session.query(ChatSession).offset(skip).limit(limit).all()

    def get_by_id(self, session_id: int) -> type[ChatSession] | None:
        chat_session = self._session.query(ChatSession).filter_by(id = session_id).first()
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return chat_session


    def create(self, chat_session: ChatSession) -> ChatSession:
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_session)
        return chat_session

    def delete_chat_session(self, session_id: int) -> type[ChatSession] | None:
        chat_session = self._session.query(ChatSession).filter_by(id = session_id).first()
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        self._session.delete(chat_session)
        self._session.commit()
        return chat_session