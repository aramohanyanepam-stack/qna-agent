import openai
from app.core.config import settings


def get_openai_client() -> openai.OpenAI | openai.AzureOpenAI:
    if settings.AZURE_ENDPOINT:
        return openai.AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_ENDPOINT
        )
    return openai.OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )