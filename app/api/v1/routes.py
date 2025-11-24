import json
from typing import Annotated, List

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.model import chat_models
from app.schema import chat_session_schemas, chat_message_schemas
from app.service.chat_message_service import ChatMessageService
from app.service.chat_session_service import ChatSessionService

router = APIRouter()


@router.post("/sessions/", response_model=chat_session_schemas.ChatSession)
def create_chat_session(
        chat_session_service: Annotated[ChatSessionService, Depends(ChatSessionService)]
):
    return chat_session_service.create()


@router.get("/sessions/", response_model=List[chat_session_schemas.ChatSession])
def read_chat_sessions(
        chat_session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
        skip: int = 0, limit: int = 100
):
    sessions = chat_session_service.get(skip=skip, limit=limit)
    return sessions


@router.get("/sessions/{session_id}", response_model=chat_session_schemas.ChatSession)
def read_chat_session(
        chat_session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
        session_id: int
):
    chat_session = chat_session_service.get_by_id(session_id=session_id)
    return chat_session


@router.delete("/sessions/{session_id}", response_model=chat_session_schemas.ChatSession)
def delete_chat_session(
        chat_session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
        session_id: int
):
    chat_session = chat_session_service.delete(session_id=session_id)
    return chat_session


@router.get("/sessions/{session_id}/messages/", response_model=List[chat_message_schemas.Message])
def read_messages(
        chat_message_service: Annotated[ChatMessageService, Depends(ChatMessageService)],
        session_id: int, skip: int = 0, limit: int = 100
):
    messages = chat_message_service.get_chat_messages_by_session_id(chat_session_id=session_id, skip=skip, limit=limit)
    return messages


@router.post("/sessions/{session_id}/messages/", response_model=chat_message_schemas.Message)
def create_message_for_session(
        chat_message_service: Annotated[ChatMessageService, Depends(ChatMessageService)],
        session_id: int, message: chat_message_schemas.MessageCreate
):
    message_model = chat_models.Message(role=message.role, content=message.content, session_id=session_id)
    user_message = chat_message_service.create_chat_message(message=message_model, session_id=session_id)
    return user_message


@router.post("/sessions/{session_id}/messages/stream")
async def create_message_for_session_stream(
        chat_message_service: Annotated[ChatMessageService, Depends(ChatMessageService)],
        session_id: int, message: chat_message_schemas.MessageCreate
) -> StreamingResponse:
    message_model = chat_models.Message(role=message.role, content=message.content, session_id=session_id)

    async def stream_generator():
        try:
            for chunk in chat_message_service.create_chat_message_stream(message=message_model, session_id=session_id):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
