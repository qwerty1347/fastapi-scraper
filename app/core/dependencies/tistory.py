from app.modules.browser.playwright import PlaywrightManager
from app.modules.llm.groq import create_async_groq_client
from app.services.llm.news_summarize import NewsSummarizeService
from app.services.scraper.finance_news import FinanceNewsScrapService
from app.services.tistory.post import TistoryPostService


def get_finance_news_scraper_service() -> FinanceNewsScrapService:
    return FinanceNewsScrapService(PlaywrightManager(headless=True))


def get_news_summarize_service() -> NewsSummarizeService:
    return NewsSummarizeService(create_async_groq_client())


def get_tistory_post_service() -> TistoryPostService:
    return TistoryPostService(PlaywrightManager(headless=True))