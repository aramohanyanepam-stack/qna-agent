# QnA-Agent: A Smart Question-Answering Agent

This project is a sophisticated Question-Answering (QnA) agent built with FastAPI. It leverages Large Language Models (LLMs) to provide intelligent, context-aware responses by retrieving information from a designated knowledge base. The agent supports both synchronous and real-time streaming responses and is designed for scalability and maintainability.

## Key Features

- **FastAPI Backend**: High-performance, asynchronous web framework.
- **Flexible LLM Integration**: Automatically connects to either a standard OpenAI-compatible API (like local models via Ollama) or Azure OpenAI, based on your environment configuration.
- **Tool-Based Knowledge Retrieval**: The agent can use tools to read from a local file-based knowledge base, allowing it to answer questions based on specific, up-to-date information.
- **Streaming and Synchronous APIs**: Provides both a standard request-response API and a real-time streaming API using Server-Sent Events (SSE).
- **SQLAlchemy ORM**: Robust database interaction layer for managing chat sessions and messages.
- **Containerized Testing**: Comprehensive integration test suite using `testcontainers` to spin up real PostgreSQL and Ollama (LLM) containers, ensuring true end-to-end validation.
- **Docker Support**: Fully containerized for easy deployment and dependency management with Docker Compose.

---

## Design Decisions

Several key design decisions were made to ensure the application is robust, scalable, and maintainable.

1.  **Modular, Layered Architecture**:
    The application is organized into a clear, layered architecture to separate concerns:
    - **Routes (`app/api/v1`)**: Handle HTTP request/response logic only.
    - **Services (`app/service`)**: Contain the core business logic. For example, `ChatMessageService` orchestrates the process of receiving a message, querying the AI, and saving the results.
    - **Repositories (`app/repository`)**: Abstract the database interaction, providing a clean interface for data access without exposing raw SQLAlchemy queries to the services.
    - **Models (`app/model`)**: Define the SQLAlchemy database schema.
    - **Schemas (`app/schema`)**: Define the Pydantic data transfer objects used for API validation and serialization.

2.  **Dynamic OpenAI Client Selection**:
    The application is designed to seamlessly switch between different LLM providers. The `app.core.openai.get_openai_client` dependency automatically detects the presence of an `AZURE_ENDPOINT` environment variable.
    - If `AZURE_ENDPOINT` **is set**, it returns an `openai.AzureOpenAI` client, using the `OPENAI_API_KEY` for authentication.
    - If `AZURE_ENDPOINT` **is not set**, it returns a standard `openai.OpenAI` client, which can be pointed to any OpenAI-compatible API, including a local Ollama instance.
    This allows the same application code to run in different environments (local development vs. Azure production) without any changes.

3.  **Tool-Based Knowledge Retrieval**:
    Instead of relying solely on the LLM's pre-trained knowledge, the agent uses a **tool-calling** approach. When asked a question, the LLM can decide to use the `get_knowledge` tool to read from files in the `./knowledge` directory. This design makes the agent's knowledge base easy to update and extend without retraining or fine-tuning the model. The system prompt (`SYSTEM_INSTRUCTION` in `query_ai_service.py`) explicitly guides the LLM on how and when to use this tool.

4.  **Robust Streaming with Data Persistence**:
    The streaming endpoint (`/messages/stream`) was designed to be resilient.
    - **Placeholder and Update Strategy**: When a streaming request begins, an empty "assistant" message is immediately saved to the database. The AI's response is streamed to the client, and the full response content is accumulated. In a `finally` block, the placeholder message in the database is updated with the full content. This ensures that even if the client disconnects mid-stream, the partial conversation is saved, providing a better user experience.
    - **Stable API Contract**: The stream yields structured `StreamEvent` Pydantic models, creating a clear, self-documenting contract with the client and decoupling it from the raw format of the underlying LLM stream.

5.  **High-Fidelity Integration Testing**:
    - **Testcontainers for True End-to-End Validation**: The integration test suite (`tests/integration`) uses `testcontainers` to spin up ephemeral Docker containers for both the **PostgreSQL database** and an **Ollama LLM**.
    - **Why this is important**: This allows tests to validate the entire application stack—from the HTTP request through the service logic, database persistence, and interaction with a *real, live LLM*—all within a fully isolated, reproducible environment. This provides a much higher degree of confidence than mocking and avoids the cost and flakiness of hitting external APIs during CI/CD.

---

## Setup and Run Instructions

### Prerequisites

- **Docker and Docker Compose**: Required to run the application and its dependencies. [Install Docker](https://docs.docker.com/get-docker/).
- **Python 3.11+** and **Poetry**: For local development and dependency management. [Install Poetry](https://python-poetry.org/docs/#installation).

### 1. Configuration

The application uses environment variables for configuration. You can choose to run with a local Ollama instance or connect to Azure OpenAI.

#### Option A: Local Development with Ollama (Default)
Create a file named `app.env` in the `env/` directory:
```bash
cp env/app.env.example env/app.env
```
This file is pre-configured to work with the local Ollama container provided in the Docker Compose setup. It does not require a real `OPENAI_API_KEY`.

#### Option B: Production with Azure OpenAI
Create a file named `app.env` in the `env/` directory and populate it with your Azure credentials:
```env
# env/app.env
OPENAI_API_KEY="YOUR_AZURE_API_KEY"
AZURE_ENDPOINT="https://your-azure-openai-instance.openai.azure.com/"
LLM_MODEL="your-azure-deployment-name" # e.g., gpt-4o
```
When you run the application, you will need to specify this environment file.

### 2. Running with Docker Compose (Recommended)

This is the easiest way to run the entire application.

- **For Local Ollama**:
  ```bash
  docker-compose up --build
  ```

The application will be available at `http://localhost:8085`.

### 3. Running Locally for Development

If you prefer to run the FastAPI server directly on your host machine:

1.  **Install Dependencies**:
    ```bash
    poetry install
    ```
2.  **Start Dependencies**:
    You still need a database. You can use Docker Compose to run just the database:
    ```bash
    docker-compose up -d postgres
    ```
3.  **Run the Application**:
    - **With Ollama**: Poetry will automatically load variables from `env/app.env`.
      ```bash
      poetry run uvicorn main:app --host 0.0.0.0 --port 8085 --reload
      ```

---

## API Usage Examples

### 1. Create a New Chat Session

```bash
curl -X POST http://localhost:8085/api/v1/chat/sessions/ -H "Content-Type: application/json" -d ''
```
**Response:**
```json
{
  "id": 1
}
```

### 2. Send a Synchronous Message

Ask a question that requires the agent to use its knowledge base.

```bash
curl -X POST http://localhost:8085/api/v1/chat/sessions/1/messages/ \
-H "Content-Type: application/json" \
-d '{
  "role": "user",
  "content": "How much does the Pro Plan cost?"
}'
```
**Response:**
```json
{
  "role": "assistant",
  "content": "The Pro Plan costs $50 per month.",
  "id": 2,
  "session_id": 1,
  "created_at": "2023-10-27T10:00:00.123456"
}
```

### 3. Send a Streaming Message

```bash
curl -N -X POST http://localhost:8085/api/v1/chat/sessions/1/messages/stream \
-H "Content-Type: application/json" \
-d '{
  "role": "user",
  "content": "What is the contact email for sales?"
}'
```
**Response (streamed as Server-Sent Events):**
```
data: {"type":"content","delta":"The"}

data: {"type":"content","delta":" contact"}

data: {"type":"content","delta":" email"}

data: {"type":"content","delta":" for"}

data: {"type":"content","delta":" sales"}

data: {"type":"content","delta":" is"}

data: {"type":"content","delta":" sales@qna-agent.com"}

data: {"type":"content","delta":"."}
```

---

## Running Tests

The test suite is divided into unit and integration tests.

1.  **Run All Tests**:
    ```bash
    poetry run pytest
    ```

2.  **Run Only Unit Tests**:
    These are fast and do not require Docker.
    ```bash
    poetry run pytest tests/
    ```

3.  **Run Only Integration Tests**:
    These tests require **Docker to be running**. By default, they use a containerized Ollama instance for the LLM.
    ```bash
    poetry run pytest -m integration
    ```

    > **:warning: Important Note on Integration Testing with Azure OpenAI**
    >
    > If you run the tests in an environment where the `AZURE_ENDPOINT` environment variable is set, the tests will **NOT** use the local Ollama container.
    >
    > Instead, the tests will connect to your **live Azure OpenAI endpoint**. This will result in **real, billable API calls** and will depend on network access to Azure.
    >
    > Always ensure your environment is configured correctly before running integration tests to avoid unexpected costs and behavior.
