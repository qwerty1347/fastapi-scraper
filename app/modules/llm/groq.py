from groq import AsyncGroq

from app.core.config import config


def create_async_groq_client() -> AsyncGroq:
    # max_retries: 429(TPM 초과) 등 일시적 오류 시 retry-after 만큼 기다렸다 자동 재시도 (기본 2 → 5)
    return AsyncGroq(api_key=config.GROQ_API_KEY, max_retries=5)