import datetime

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
from app.service.chat_session_service import ChatSessionService
from app.schema.chat_session_schemas import ChatSession

# Mock the service dependency
mock_chat_session_service = MagicMock()

def override_chat_session_service():
    return mock_chat_session_service

# Apply the dependency override to the app
app.dependency_overrides[ChatSessionService] = override_chat_session_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    mock_chat_session_service.reset_mock()

def test_create_chat_session():
    # Arrange
    created_at = datetime.datetime.now()
    mock_session = ChatSession(id=1, created_at=created_at)
    mock_chat_session_service.create.return_value = mock_session
    
    # Act
    response = client.post("/api/v1/chat/sessions/")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": 1, "created_at": created_at.isoformat(), "messages": []}
    mock_chat_session_service.create.assert_called_once()

def test_read_chat_sessions():
    # Arrange
    created_at = datetime.datetime.now()
    mock_sessions = [ChatSession(id=1, created_at=created_at), ChatSession(id=2, created_at=created_at)]
    mock_chat_session_service.get.return_value = mock_sessions
    
    # Act
    response = client.get("/api/v1/chat/sessions/?skip=0&limit=10")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "created_at": created_at.isoformat(), "messages": []}, {"id": 2, "created_at": created_at.isoformat(), "messages": []}]
    mock_chat_session_service.get.assert_called_once_with(skip=0, limit=10)

def test_read_chat_session():
    # Arrange
    session_id = 1
    created_at = datetime.datetime.now()
    mock_session = ChatSession(id=session_id, created_at=created_at)
    mock_chat_session_service.get_by_id.return_value = mock_session
    
    # Act
    response = client.get(f"/api/v1/chat/sessions/{session_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": session_id, "created_at": created_at.isoformat(), "messages": []}
    mock_chat_session_service.get_by_id.assert_called_once_with(session_id=session_id)

def test_delete_chat_session():
    # Arrange
    session_id = 1
    created_at = datetime.datetime.now()
    mock_session = ChatSession(id=session_id, created_at=created_at)
    mock_chat_session_service.delete.return_value = mock_session
    
    # Act
    response = client.delete(f"/api/v1/chat/sessions/{session_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": session_id, "created_at": created_at.isoformat(), "messages": []}
    mock_chat_session_service.delete.assert_called_once_with(session_id=session_id)
