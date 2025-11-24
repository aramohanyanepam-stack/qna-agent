import json
import os
from typing import List, Generator

import openai
from fastapi import Depends
from openai.types.chat import ChatCompletionFunctionToolParam, ChatCompletionMessageParam, \
    ChatCompletionToolMessageParam, ChatCompletionAssistantMessageParam, ChatCompletionUserMessageParam, \
    ChatCompletionSystemMessageParam, ChatCompletionMessageFunctionToolCallParam
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_message_function_tool_call_param import Function

from app.core.config import settings
from app.core.openai import get_openai_client
from app.schema.chat_message_schemas import MessageBase

MESSAGE_TYPES = {
    "user": lambda role, content: ChatCompletionUserMessageParam(role=role, content=content),
    "assistant": lambda role, content: ChatCompletionAssistantMessageParam(role=role, content=content),
    "system": lambda role, content: ChatCompletionSystemMessageParam(role=role, content=content)
}

SYSTEM_INSTRUCTION = """
You are a helpful assistant that answers questions.
When a user asks a question, you should use the get_knowledge tool to find the relevant information from the knowledge base.
The knowledge base is organized into several files, and you need to select the correct file to answer the user's question.
The available files are:
- product_info.txt: General information about the QnA-Agent product.
- faq.txt: Frequently asked questions and answers.
- pricing.txt: Details about different pricing plans.
- contact_info.txt: Contact details for sales and support.
- api_reference.txt: Technical specifications for the API.

Carefully consider the user's question to determine which file is most likely to contain the answer.
Use file_name param of get_knowledge method to choose the corresponding file. 
"""


def map_message_to_message_param(messages: List[MessageBase]) -> List[ChatCompletionMessageParam]:
    return [MESSAGE_TYPES.get(msg.role, lambda role, content: ChatCompletionUserMessageParam(role=role, content=content))
            (msg.role, msg.content) for msg in messages]


def get_knowledge(file_name: str) -> str:
    """
    Retrieves content from a file in the knowledge base.
    """
    file_path = os.path.join(settings.KNOWLEDGE_BASE_DIR, file_name)
    if not os.path.exists(file_path):
        return f"Error: File '{file_name}' not found in the knowledge base."
    if os.path.isdir(file_path):
        return f"Error: '{file_name}' is a directory, not a file."
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{file_name}': {e}"


class QueryAIService:
    def __init__(self, client: openai.OpenAI | openai.AzureOpenAI = Depends(get_openai_client)):
        self.temperature = settings.LLM_TEMPERATURE
        self.client = client
        self.tools: List[ChatCompletionFunctionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": "get_knowledge",
                    "description": "Get information from a file in the knowledge base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_name": {
                                "type": "string",
                                "description": "The name of the file to read from the knowledge base.",
                            },
                        },
                        "required": ["file_name"],
                    },
                },
            }
        ]

    @staticmethod
    def _prepare_message_params(messages: List[MessageBase]) -> List[ChatCompletionMessageParam]:
        message_params = [ChatCompletionSystemMessageParam(role="system", content=SYSTEM_INSTRUCTION)]
        message_params.extend(map_message_to_message_param(messages))
        return message_params

    @staticmethod
    def _handle_tool_calls(message_params: List[ChatCompletionMessageParam], tool_calls, full_content: str):
        """Handle tool calls and return the final response."""
        message_params.append(ChatCompletionAssistantMessageParam(
            role="assistant",
            tool_calls=[
                ChatCompletionMessageFunctionToolCallParam(
                    id=tool_call.id,
                    function=Function(name=tool_call.function.name, arguments=tool_call.function.arguments),
                    type="function"
                )
                for tool_call in tool_calls
            ],
            content=full_content
        ))

        available_functions = {"get_knowledge": get_knowledge}
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_response = available_functions[function_name](
                file_name=json.loads(tool_call.function.arguments).get("file_name")
            )
            message_params.append(ChatCompletionToolMessageParam(
                tool_call_id=tool_call.id,
                role="tool",
                content=function_response
            ))

        return message_params

    def query_ai_stream(self, messages: List[MessageBase], llm_model=settings.LLM_MODEL) -> Generator[str, None, None]:
        """Streaming version of query_ai that yields response chunks."""
        try:
            message_params = self._prepare_message_params(messages)

            # Initial streaming request
            stream = self.client.chat.completions.create(
                model=llm_model,
                messages=message_params,
                temperature=self.temperature,
                tools=self.tools,
                tool_choice="auto",
                stream=True,
            )

            # Collect full response from stream
            full_content = ""
            tool_calls = []

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    yield delta.content
                if delta.tool_calls:
                    tool_calls.extend(delta.tool_calls)

            # Handle tool calls if present
            if tool_calls:
                message_params = self._handle_tool_calls(message_params, tool_calls, full_content)

                # Second request for final response
                second_stream = self.client.chat.completions.create(
                    model=llm_model,
                    messages=message_params,
                    tools=self.tools,
                    stream=True,
                )
                for chunk in second_stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        except openai.APIStatusError as e:
            raise RuntimeError(f"Service OpenAI returned an API error (Status Code: {e.status_code})") from e
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"An unexpected error occurred: {str(e)}"
            raise RuntimeError(f"{error_message} (Error Type: {error_type})") from e

    def query_ai(self, messages: List[MessageBase], llm_model=settings.LLM_MODEL):
        # This method remains for non-streaming purposes
        try:
            message_params = self._prepare_message_params(messages)
            response = self.client.chat.completions.create(
                model=llm_model,
                messages=message_params,
                temperature=self.temperature,
                tools=self.tools,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                message_params = self._handle_tool_calls(message_params, tool_calls, response_message.content)
                second_response = self.client.chat.completions.create(
                    model=llm_model,
                    messages=message_params,
                    tools=self.tools,
                )
                return second_response.choices[0].message.content, response.id

            return response_message.content, response.id

        except openai.APIStatusError as e:
            raise RuntimeError(f"Service OpenAI returned an API error (Status Code: {e.status_code})") from e
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"An unexpected error occurred: {str(e)}"
            raise RuntimeError(f"{error_message} (Error Type: {error_type})") from e
