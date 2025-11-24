import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from main import app
from app.model.chat_models import ChatSession, Message
import json

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_integration_test(override_get_db, monkeypatch):
    """
    Ensures database and AI service dependencies are overridden for each test.
    This uses a real database and a real (containerized) LLM.
    It also sets the model to one that exists in the container.
    """
    # monkeypatch.setattr("app.core.config.settings.LLM_MODEL", "phi3:mini")
    yield

@pytest.mark.integration
def test_create_chat_session(db_session):
    response = client.post("/api/v1/chat/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] is not None

    # Verify in DB
    session_in_db = db_session.query(ChatSession).filter_by(id=data["id"]).first()
    assert session_in_db is not None
    assert session_in_db.id == data["id"]

@pytest.mark.integration
def test_read_chat_sessions(db_session):
    # Arrange: Create a few sessions directly in DB
    session1 = ChatSession()
    session2 = ChatSession()
    db_session.add_all([session1, session2])
    db_session.commit()
    db_session.refresh(session1)
    db_session.refresh(session2)

    response = client.get("/api/v1/chat/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(s["id"] == session1.id for s in data)
    assert any(s["id"] == session2.id for s in data)

@pytest.mark.integration
def test_read_chat_session(db_session):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    response = client.get(f"/api/v1/chat/sessions/{session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session.id

@pytest.mark.integration
def test_read_chat_session_not_found():
    response = client.get("/api/v1/chat/sessions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found"}

@pytest.mark.integration
def test_delete_chat_session(db_session):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    response = client.delete(f"/api/v1/chat/sessions/{session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session.id

    # Verify deletion in DB
    session_in_db = db_session.query(ChatSession).filter_by(id=session.id).first()
    assert session_in_db is None

@pytest.mark.integration
def test_delete_chat_session_not_found():
    response = client.delete("/api/v1/chat/sessions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found"}


@pytest.mark.integration
def test_create_message_for_session(db_session):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    user_message_content = "How much is the Basic Plan?"
    request_data = {"role": "user", "content": user_message_content}

    # Act
    response = client.post(f"/api/v1/chat/sessions/{session.id}/messages/", json=request_data)
    assert response.status_code == 200
    response_data = response.json()

    # Assert response structure
    assert "id" in response_data
    assert response_data["role"] == "assistant"
    assert response_data["session_id"] == session.id
    
    # Assert content from the real LLM
    final_answer = response_data["content"]
    assert "$10" in final_answer
    assert "month" in final_answer

    # Verify messages in DB
    messages_in_db = db_session.query(Message).filter_by(session_id=session.id).order_by(Message.id).all()
    assert len(messages_in_db) == 2
    assert messages_in_db[0].role == "user"
    assert messages_in_db[0].content == user_message_content
    assert messages_in_db[1].role == "assistant"
    assert messages_in_db[1].content == final_answer


@pytest.mark.integration
def test_create_message_for_session_stream(db_session):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    user_message_content = "What is the contact email for sales?"
    request_data = {"role": "user", "content": user_message_content}

    # Act
    response = client.post(f"/api/v1/chat/sessions/{session.id}/messages/stream", json=request_data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Process and verify the streaming response
    full_response_content = ""
    
    for line in response.iter_lines():
        if line.startswith("data:"):
            data_str = line[len("data: "):]
            try:
                chunk = json.loads(data_str)
                if chunk.get("type") == "content":
                    full_response_content += chunk.get("delta", "")
            except json.JSONDecodeError:
                continue

    # Assert that the key events occurred
    assert "sales@qna-agent.com" in full_response_content

    # Verify messages in DB
    messages_in_db = db_session.query(Message).filter_by(session_id=session.id).order_by(Message.id).all()
    assert len(messages_in_db) == 2
    assert messages_in_db[0].role == "user"
    assert messages_in_db[0].content == user_message_content
    assert messages_in_db[1].role == "assistant"
    assert messages_in_db[1].content == full_response_content


@pytest.mark.integration
def test_create_message_for_session_with_llm_validation(db_session, openai_client):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    user_message_content = "What is the QnA-Agent and what are its main features?"
    request_data = {"role": "user", "content": user_message_content}

    # Act: Get the application's response
    response = client.post(f"/api/v1/chat/sessions/{session.id}/messages/", json=request_data)
    assert response.status_code == 200
    response_data = response.json()
    app_generated_answer = response_data["content"]

    # Assert: Use a separate LLM call to validate the response
    validation_prompt = f"""
    The user asked: "{user_message_content}"
    The application answered: "{app_generated_answer}"
    
    Based on the provided context about the QnA-Agent (a smart question-answering agent with features like tool use,
     streaming, and Docker support), is the application's answer helpful and accurate? 
    Respond with only "Yes" or "No".
    """

    validation_response = openai_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{'role': 'user', 'content': validation_prompt}]
    )
    
    assert "yes" in validation_response.choices[0].message.content.lower()


@pytest.mark.integration
def test_create_message_for_session_stream_with_llm_validation(db_session, openai_client):
    # Arrange: Create a session
    session = ChatSession()
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    user_message_content = "What are the main features of the QnA-Agent?"
    request_data = {"role": "user", "content": user_message_content}

    # Act
    response = client.post(f"/api/v1/chat/sessions/{session.id}/messages/stream", json=request_data)
    assert response.status_code == 200

    full_response_content = ""
    for line in response.iter_lines():
        if line.startswith("data:"):
            data_str = line[len("data: "):]
            try:
                chunk = json.loads(data_str)
                if chunk.get("type") == "content":
                    full_response_content += chunk.get("delta", "")
            except json.JSONDecodeError:
                continue

    # Assert: Use a separate LLM call to validate the streamed response
    validation_prompt = f"""
    The user asked: "{user_message_content}"
    The application's streamed answer was: "{full_response_content}"

    Does the answer correctly list features like Natural Language Understanding, Tool Usage, and Streaming Responses?
    Respond with only "Yes" or "No".
    """

    validation_response = openai_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{'role': 'user', 'content': validation_prompt}]
    )

    assert "yes" in validation_response.choices[0].message.content.lower()
