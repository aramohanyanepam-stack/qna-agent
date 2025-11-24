from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./chat.db"
    DATABASE_USER_NAME: str = ""
    DATABASE_PASSWORD: str = ""
    DATABASE_HOST: str = ""
    DATABASE_PORT: str = ""
    LLM_MODEL: str = "gpt-4o-mini-2024-07-18"
    LLM_TEMPERATURE: float = 0.7
    OPENAI_API_KEY: str = ""
    AZURE_ENDPOINT: str = ""
    OPENAI_BASE_URL: str = "http://localhost:11434/v1/"
    OPENAI_API_VERSION: str = "2023-07-01-preview"
    KNOWLEDGE_BASE_DIR: str = "knowledge"
    model_config = SettingsConfigDict(env_file='env/app.env')


settings = Settings()