import pytest
from unittest.mock import MagicMock, call
from app.service.chat_message_service import ChatMessageService
from app.model.chat_models import Message
from app.schema.chat_message_schemas import MessageBase, StreamContent

@pytest.fixture
def mock_chat_message_repository():
    return MagicMock()

@pytest.fixture
def mock_query_ai_service():
    return MagicMock()

@pytest.fixture
def chat_message_service(mock_chat_message_repository, mock_query_ai_service):
    return ChatMessageService(
        repository=mock_chat_message_repository,
        query_ai_service=mock_query_ai_service
    )

def test_get_chat_messages_by_session_id(chat_message_service, mock_chat_message_repository):
    # Arrange
    session_id = 1
    mock_chat_message_repository.get_by_session_id.return_value = [Message(id=1, session_id=session_id)]
    
    # Act
    result = chat_message_service.get_chat_messages_by_session_id(session_id, 0, 100)
    
    # Assert
    assert len(result) == 1
    mock_chat_message_repository.get_by_session_id.assert_called_once_with(session_id, 0, 100)

def test_create_chat_message(chat_message_service, mock_chat_message_repository, mock_query_ai_service):
    # Arrange
    session_id = 1
    user_message = Message(role="user", content="Hello", session_id=session_id)
    ai_message = Message(role="assistant", content="AI response", session_id=session_id)

    mock_chat_message_repository.get_by_session_id.return_value = [user_message]
    mock_query_ai_service.query_ai.return_value = ("AI response", "response_id")
    mock_chat_message_repository.create.side_effect = [user_message, ai_message]
    
    # Act
    result = chat_message_service.create_chat_message(user_message, session_id)
    
    # Assert
    create_calls = mock_chat_message_repository.create.call_args_list
    assert len(create_calls) == 2
    assert create_calls[0] == call(message=user_message)
    
    # Inspect the second call's arguments
    second_call_args = create_calls[1][1]
    assert second_call_args['message'].role == "assistant"
    assert second_call_args['message'].content == "AI response"

    mock_chat_message_repository.get_by_session_id.assert_called_once_with(session_id=session_id)
    mock_query_ai_service.query_ai.assert_called_once_with([MessageBase(role="user", content="Hello")])
    assert result.role == "assistant"
    assert result.content == "AI response"

def test_create_chat_message_stream(chat_message_service, mock_chat_message_repository, mock_query_ai_service):
    # Arrange
    session_id = 1
    user_message = Message(role="user", content="Hello", session_id=session_id)
    
    mock_chat_message_repository.get_by_session_id.return_value = [user_message]
    mock_query_ai_service.query_ai_stream.return_value = iter([
        {"type": "content", "delta": "AI "},
        {"type": "content", "delta": "response"}
    ])
    
    # Act
    result = list(chat_message_service.create_chat_message_stream(user_message, session_id))
    
    # Assert
    # 1. Verify the user message and a placeholder AI message were created.
    create_calls = mock_chat_message_repository.create.call_args_list
    assert len(create_calls) == 2
    assert create_calls[0].kwargs['message'] is user_message
    
    placeholder_message = create_calls[1].kwargs['message']
    assert placeholder_message.role == "assistant"
    
    # 2. Verify the stream content is correct.
    assert len(result) == 2
    assert isinstance(result[0], StreamContent) and result[0].delta == "AI "
    assert isinstance(result[1], StreamContent) and result[1].delta == "response"
    
    # 3. Verify the placeholder was updated with the final content.
    mock_chat_message_repository.update.assert_called_once()
    updated_message = mock_chat_message_repository.update.call_args.kwargs['message']
    
    # 4. Crucially, verify the object created as a placeholder is the SAME object that was updated.
    assert updated_message is placeholder_message
    assert updated_message.content == "AI response"

    # 5. Verify other service calls.
    mock_chat_message_repository.get_by_session_id.assert_called_once_with(session_id=session_id)
    mock_query_ai_service.query_ai_stream.assert_called_once_with([MessageBase(role="user", content="Hello")])
