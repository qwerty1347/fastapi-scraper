from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies.tistory import get_finance_news_scraper_service, get_news_summarize_service, get_tistory_post_service
from app.core.utils.response import success_response
from app.prompts.finance_news import FINANCE_NEWS_SYSTEM_PROMPT
from app.schemas.base import BaseResponse
from app.schemas.tistory.article import NewsArticle, SummarizedArticle
from app.schemas.tistory.request import TistoryPublishRequest, TistorySummarizeRequest
from app.schemas.tistory.response import PostingResponse
from app.services.llm.news_summarize import NewsSummarizeService
from app.services.scraper.finance_news import FinanceNewsScrapService
from app.services.tistory.post import TistoryPostService


router = APIRouter(prefix="/finance")

@router.get('/', response_model=BaseResponse)
def index() -> JSONResponse:
    return success_response()


@router.get('/scrap', response_model=BaseResponse[list[NewsArticle]])
async def scrap(
    finance_scrap: Annotated[FinanceNewsScrapService, Depends(get_finance_news_scraper_service)]
) -> JSONResponse:
    response = await finance_scrap.do_scraping()
    return success_response({'articles': response})


@router.post('/summarize', response_model=BaseResponse[list[SummarizedArticle]])
async def summarize(
    payload: TistorySummarizeRequest,
    summarize_service: Annotated[NewsSummarizeService, Depends(get_news_summarize_service)]
) -> JSONResponse:
    summarized_articles = await summarize_service.summarize_many(payload.articles, FINANCE_NEWS_SYSTEM_PROMPT)
    return success_response({'summarized_articles': summarized_articles})


@router.post('/publish', response_model=BaseResponse[PostingResponse])
async def publish(
    payload: TistoryPublishRequest,
    tistory_post_service: Annotated[TistoryPostService, Depends(get_tistory_post_service)]
) -> JSONResponse:
    response = await tistory_post_service.do_posting(payload.blog_category, payload.summarized_articles, payload.reservation_data)
    return success_response({'response': response})


@router.post('/run')
async def run() -> JSONResponse:
    return success_response()
    # todo: 자동 포스팅