import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.repository.chat_session_repository import ChatSessionRepository
from app.model.chat_models import ChatSession

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def chat_session_repository(mock_db_session):
    return ChatSessionRepository(db=mock_db_session)

def test_get(chat_session_repository, mock_db_session):
    # Arrange
    mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [ChatSession(id=1), ChatSession(id=2)]

    # Act
    result = chat_session_repository.get(skip=0, limit=100)

    # Assert
    assert len(result) == 2
    mock_db_session.query.assert_called_once_with(ChatSession)
    mock_db_session.query.return_value.offset.assert_called_once_with(0)
    mock_db_session.query.return_value.offset.return_value.limit.assert_called_once_with(100)
    mock_db_session.query.return_value.offset.return_value.limit.return_value.all.assert_called_once()

def test_get_by_id_found(chat_session_repository, mock_db_session):
    # Arrange
    mock_session = ChatSession(id=1)
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_session

    # Act
    result = chat_session_repository.get_by_id(session_id=1)

    # Assert
    assert result == mock_session
    mock_db_session.query.assert_called_once_with(ChatSession)
    mock_db_session.query.return_value.filter_by.assert_called_once_with(id=1)
    mock_db_session.query.return_value.filter_by.return_value.first.assert_called_once()

def test_get_by_id_not_found(chat_session_repository, mock_db_session):
    # Arrange
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        chat_session_repository.get_by_id(session_id=1)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"

def test_create(chat_session_repository, mock_db_session):
    # Arrange
    chat_session = ChatSession(id=1)

    # Act
    result = chat_session_repository.create(chat_session)

    # Assert
    assert result == chat_session
    mock_db_session.add.assert_called_once_with(chat_session)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(chat_session)

def test_delete_chat_session_found(chat_session_repository, mock_db_session):
    # Arrange
    mock_session = ChatSession(id=1)
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_session

    # Act
    result = chat_session_repository.delete_chat_session(session_id=1)

    # Assert
    assert result == mock_session
    mock_db_session.delete.assert_called_once_with(mock_session)
    mock_db_session.commit.assert_called_once()

def test_delete_chat_session_not_found(chat_session_repository, mock_db_session):
    # Arrange
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        chat_session_repository.delete_chat_session(session_id=1)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Chat session not found"
