import pytest
from unittest.mock import MagicMock, call
from app.service.chat_session_service import ChatSessionService
from app.model.chat_models import ChatSession

@pytest.fixture
def mock_chat_session_repository():
    return MagicMock()

@pytest.fixture
def chat_session_service(mock_chat_session_repository):
    return ChatSessionService(repository=mock_chat_session_repository)

def test_get(chat_session_service, mock_chat_session_repository):
    # Arrange
    mock_chat_session_repository.get.return_value = [ChatSession(id=1), ChatSession(id=2)]
    
    # Act
    result = chat_session_service.get(0, 100)
    
    # Assert
    assert len(result) == 2
    mock_chat_session_repository.get.assert_called_once_with(0, 100)

def test_get_by_id(chat_session_service, mock_chat_session_repository):
    # Arrange
    session_id = 1
    mock_chat_session_repository.get_by_id.return_value = ChatSession(id=session_id)
    
    # Act
    result = chat_session_service.get_by_id(session_id)
    
    # Assert
    assert result.id == session_id
    mock_chat_session_repository.get_by_id.assert_called_once_with(session_id)

def test_create(chat_session_service, mock_chat_session_repository):
    # Arrange
    mock_chat_session_repository.create.return_value = ChatSession(id=1)
    
    # Act
    result = chat_session_service.create()
    
    # Assert
    assert result.id == 1
    # Verify that the create method was called with a ChatSession instance
    create_call = mock_chat_session_repository.create.call_args
    assert create_call is not None
    assert isinstance(create_call[0][0], ChatSession)

def test_delete(chat_session_service, mock_chat_session_repository):
    # Arrange
    session_id = 1
    mock_chat_session_repository.delete_chat_session.return_value = ChatSession(id=session_id)
    
    # Act
    result = chat_session_service.delete(session_id)
    
    # Assert
    assert result.id == session_id
    mock_chat_session_repository.delete_chat_session.assert_called_once_with(session_id)
