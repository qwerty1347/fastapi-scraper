from groq import AsyncGroq

from app.core.config import config


def create_async_groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=config.GROQ_API_KEY)