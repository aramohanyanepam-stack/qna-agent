from typing import Annotated
from fastapi import Depends
from app.model.chat_models import ChatSession
from app.repository.chat_session_repository import ChatSessionRepository


class ChatSessionService:
    def __init__(self, repository: Annotated[ChatSessionRepository, Depends(ChatSessionRepository)]):
        self.repository = repository

    def get(self, skip: int = 0, limit: int = 100) -> list[type[ChatSession]]:
        return self.repository.get(skip, limit)

    def get_by_id(self, session_id: int) -> type[ChatSession] | None:
        return self.repository.get_by_id(session_id)

    def create(self) -> ChatSession:
        chat_session = ChatSession()
        return self.repository.create(chat_session)

    def delete(self, session_id: int) -> type[ChatSession] | None:
        return self.repository.delete_chat_session(session_id)
