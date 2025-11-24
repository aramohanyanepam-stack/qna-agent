import pytest
from unittest.mock import MagicMock, patch
from app.service.query_ai_service import QueryAIService
from app.schema.chat_message_schemas import MessageBase
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta, ChoiceDeltaToolCall
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function as ToolFunction
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCallFunction
from openai.types.completion_usage import CompletionUsage

@pytest.fixture
def mock_openai_client():
    return MagicMock()

@pytest.fixture
def query_ai_service(mock_openai_client):
    return QueryAIService(client=mock_openai_client)

@pytest.fixture
def sample_messages():
    return [MessageBase(role="user", content="Hello")]

def test_query_ai_simple(query_ai_service, mock_openai_client, sample_messages):
    # Arrange
    mock_response = ChatCompletion(
        id="chatcmpl-123",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="Hello there!",
                    tool_calls=None
                ),
            )
        ],
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=5, total_tokens=10),
        created=1677652088,
        system_fingerprint="fp_44709d6fcb",
    )
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Act
    content, response_id = query_ai_service.query_ai(sample_messages)

    # Assert
    assert content == "Hello there!"
    assert response_id == "chatcmpl-123"
    mock_openai_client.chat.completions.create.assert_called_once()

def test_query_ai_with_tool_call(query_ai_service, mock_openai_client, sample_messages):
    # Arrange
    tool_call = ChatCompletionMessageToolCall(
        id="call_123",
        function=ToolFunction(name="get_knowledge", arguments='{"file_name": "faq.txt"}'),
        type="function"
    )
    
    # First response with tool call
    mock_response1 = ChatCompletion(
        id="chatcmpl-123",
        choices=[
            Choice(
                finish_reason="tool_calls",
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[tool_call]
                ),
            )
        ],
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=5, total_tokens=10),
        created=1677652088,
        system_fingerprint="fp_44709d6fcb",
    )

    # Second response after tool execution
    mock_response2 = ChatCompletion(
        id="chatcmpl-456",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="The answer is in the FAQ.",
                    tool_calls=None
                ),
            )
        ],
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        usage=CompletionUsage(completion_tokens=5, prompt_tokens=5, total_tokens=10),
        created=1677652088,
        system_fingerprint="fp_44709d6fcb",
    )
    
    mock_openai_client.chat.completions.create.side_effect = [mock_response1, mock_response2]

    with patch('app.service.query_ai_service.get_knowledge', return_value="FAQ content") as mock_get_knowledge:
        # Act
        content, response_id = query_ai_service.query_ai(sample_messages)

        # Assert
        assert content == "The answer is in the FAQ."
        assert response_id == "chatcmpl-123"
        mock_get_knowledge.assert_called_once_with(file_name="faq.txt")
        assert mock_openai_client.chat.completions.create.call_count == 2

def test_query_ai_stream_simple(query_ai_service, mock_openai_client, sample_messages):
    # Arrange
    mock_chunks = [
        ChatCompletionChunk(
            id="chunk-123",
            choices=[ChunkChoice(delta=ChoiceDelta(content="Hello"), finish_reason=None, index=0)],
            model="gpt-4o-mini-2024-07-18",
            object="chat.completion.chunk",
            created=1677652088,
        ),
        ChatCompletionChunk(
            id="chunk-124",
            choices=[ChunkChoice(delta=ChoiceDelta(content=" there!"), finish_reason=None, index=0)],
            model="gpt-4o-mini-2024-07-18",
            object="chat.completion.chunk",
            created=1677652088,
        )
    ]
    mock_openai_client.chat.completions.create.return_value = mock_chunks

    # Act
    result = list(query_ai_service.query_ai_stream(sample_messages))

    # Assert
    assert "".join(chunk for chunk in result) == "Hello there!"
    mock_openai_client.chat.completions.create.assert_called_once()

def test_query_ai_stream_with_tool_call(query_ai_service, mock_openai_client, sample_messages):
    # Arrange
    tool_call_chunk = ChoiceDelta(
        content=None,
        role='assistant',
        tool_calls=[
            ChoiceDeltaToolCall(index=0, id='call_123', function=ChoiceDeltaToolCallFunction(name='get_knowledge', arguments='{"file_name": "faq.txt"}'), type='function')
        ]
    )
    
    # First stream with tool call
    mock_stream1 = [
        ChatCompletionChunk(
            id="chunk-123",
            choices=[ChunkChoice(delta=tool_call_chunk, finish_reason="tool_calls", index=0)],
            model="gpt-4o-mini-2024-07-18",
            object="chat.completion.chunk",
            created=1677652088,
        )
    ]

    # Second stream after tool execution
    mock_stream2 = [
        ChatCompletionChunk(
            id="chunk-456",
            choices=[ChunkChoice(delta=ChoiceDelta(content="The answer is in the FAQ."), finish_reason=None, index=0)],
            model="gpt-4o-mini-2024-07-18",
            object="chat.completion.chunk",
            created=1677652088,
        )
    ]
    
    mock_openai_client.chat.completions.create.side_effect = [mock_stream1, mock_stream2]

    with patch('app.service.query_ai_service.get_knowledge', return_value="FAQ content") as mock_get_knowledge:
        # Act
        result = list(query_ai_service.query_ai_stream(sample_messages))

        # Assert
        assert "".join(result) == "The answer is in the FAQ."
        mock_get_knowledge.assert_called_once_with(file_name="faq.txt")
        assert mock_openai_client.chat.completions.create.call_count == 2
