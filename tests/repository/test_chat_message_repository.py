import pytest
from unittest.mock import MagicMock
from app.repository.chat_message_repository import ChatMessageRepository
from app.model.chat_models import Message

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def chat_message_repository(mock_db_session):
    return ChatMessageRepository(db=mock_db_session)

def test_get_by_session_id(chat_message_repository, mock_db_session):
    # Arrange
    session_id = 1
    mock_db_session.query.return_value.filter_by.return_value.offset.return_value.limit.return_value.all.return_value = [Message(id=1, session_id=session_id)]
    
    # Act
    result = chat_message_repository.get_by_session_id(session_id=session_id, skip=0, limit=100)
    
    # Assert
    assert len(result) == 1
    assert result[0].session_id == session_id
    mock_db_session.query.assert_called_once_with(Message)
    mock_db_session.query.return_value.filter_by.assert_called_once_with(session_id=session_id)
    mock_db_session.query.return_value.filter_by.return_value.offset.assert_called_once_with(0)
    mock_db_session.query.return_value.filter_by.return_value.offset.return_value.limit.assert_called_once_with(100)
    mock_db_session.query.return_value.filter_by.return_value.offset.return_value.limit.return_value.all.assert_called_once()

def test_create(chat_message_repository, mock_db_session):
    # Arrange
    message = Message(id=1, role="user", content="Hello", session_id=1)
    
    # Act
    result = chat_message_repository.create(message)
    
    # Assert
    assert result == message
    mock_db_session.add.assert_called_once_with(message)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(message)

def test_update(chat_message_repository, mock_db_session):
    # Arrange
    message = Message(id=1, role="user", content="Hello", session_id=1)
    
    # Act
    result = chat_message_repository.update(message)
    
    # Assert
    assert result == message
    mock_db_session.add.assert_called_once_with(message)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(message)
