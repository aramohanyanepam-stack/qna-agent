from typing import Annotated, List, Type, Generator

from fastapi import Depends

from app.schema.chat_message_schemas import MessageBase, StreamEvent, StreamContent, StreamToolStart, StreamToolEnd
from app.service.query_ai_service import QueryAIService
from app.model.chat_models import Message
from app.repository.chat_message_repository import ChatMessageRepository


class ChatMessageService:
    def __init__(
            self,
            repository: Annotated[ChatMessageRepository, Depends(ChatMessageRepository)],
            query_ai_service: Annotated[QueryAIService, Depends(QueryAIService)]
    ):
        self.repository = repository
        self.query_ai_service = query_ai_service

    def get_chat_messages_by_session_id(self, chat_session_id: int, skip: int = 0,
                                        limit: int = 100) -> List[Type[Message]]:
        return self.repository.get_by_session_id(chat_session_id, skip, limit)

    def create_chat_message(self, message: Message, session_id) -> Message:
        self.repository.create(message=message)

        history = self.repository.get_by_session_id(session_id=session_id)
        messages = [MessageBase(role=msg.role, content=msg.content) for msg in history]

        ai_response_content, _ = self.query_ai_service.query_ai(messages)

        ai_message = Message(role="assistant", content=ai_response_content, session_id=session_id)
        return self.repository.create(message=ai_message)

    def create_chat_message_stream(self, message: Message, session_id: int) -> Generator[StreamEvent, None, None]:
        self.repository.create(message=message)

        history = self.repository.get_by_session_id(session_id=session_id)
        messages = [MessageBase(role=msg.role, content=msg.content) for msg in history]

        # Create a placeholder for the assistant's message
        ai_message = Message(role="assistant", content="", session_id=session_id)
        self.repository.create(message=ai_message)

        response_stream = self.query_ai_service.query_ai_stream(messages)

        ai_response_content = ""
        try:
            for chunk in response_stream:
                ai_response_content += chunk
                yield StreamContent(type="content", delta=chunk)

        finally:
            # Update the placeholder with the final content
            ai_message.content = ai_response_content
            self.repository.update(message=ai_message)
