import pytest
import json
import datetime
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from app.service.chat_message_service import ChatMessageService
from app.schema.chat_message_schemas import Message, StreamContent, StreamToolStart
from app.model.chat_models import Message as MessageModel

# Mock the service dependency
mock_chat_message_service = MagicMock()

def override_chat_message_service():
    return mock_chat_message_service

# Apply the dependency override to the app
app.dependency_overrides[ChatMessageService] = override_chat_message_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    mock_chat_message_service.reset_mock()

def test_create_message_for_session():
    # Arrange
    session_id = 1
    request_data = {"role": "user", "content": "Hello"}
    
    # The service is expected to return a full Message schema object
    mock_response_message = Message(
        id=1,
        session_id=session_id,
        role="assistant",
        content="AI response",
        created_at=datetime.datetime.now()
    )
    mock_chat_message_service.create_chat_message.return_value = mock_response_message
    
    # Act
    response = client.post(f"/api/v1/chat/sessions/{session_id}/messages/", json=request_data)
    
    # Assert
    assert response.status_code == 200
    response_json = response.json()
    # Pydantic models will convert datetimes to ISO strings
    assert response_json["content"] == "AI response"
    assert response_json["role"] == "assistant"
    
    # Verify that the service was called correctly
    mock_chat_message_service.create_chat_message.assert_called_once()
    call_args = mock_chat_message_service.create_chat_message.call_args
    # The first argument is the Message model instance
    assert isinstance(call_args.kwargs['message'], MessageModel)
    assert call_args.kwargs['message'].content == "Hello"
    assert call_args.kwargs['session_id'] == session_id

def test_create_message_for_session_stream():
    # Arrange
    session_id = 1
    request_data = {"role": "user", "content": "What is the price?"}
    
    # The service is expected to return a generator of StreamEvent models
    mock_stream_events = [
        StreamToolStart(type="tool_start", name="get_knowledge"),
        StreamContent(type="content", delta="The price is $10."),
    ]
    mock_chat_message_service.create_chat_message_stream.return_value = iter(mock_stream_events)
    
    # Act
    response = client.post(f"/api/v1/chat/sessions/{session_id}/messages/stream", json=request_data)
    
    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Manually parse the Server-Sent Events (SSE) response
    lines = response.text.split('\n\n')
    # Filter out any empty strings from the split
    sse_events = [line for line in lines if line]
    
    assert len(sse_events) == 2
    
    # Verify first event
    event1_data = json.loads(sse_events[0].replace("data: ", ""))
    assert event1_data == {"type": "tool_start", "name": "get_knowledge"}
    
    # Verify second event
    event2_data = json.loads(sse_events[1].replace("data: ", ""))
    assert event2_data == {"type": "content", "delta": "The price is $10."}
    
    # Verify that the service was called correctly
    mock_chat_message_service.create_chat_message_stream.assert_called_once()
    call_args = mock_chat_message_service.create_chat_message_stream.call_args
    assert isinstance(call_args.kwargs['message'], MessageModel)
    assert call_args.kwargs['message'].content == "What is the price?"
    assert call_args.kwargs['session_id'] == session_id
