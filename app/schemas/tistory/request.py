from pydantic import BaseModel

from app.schemas.tistory.article import FinanceArticle, ReservationData, SummarizedArticle


class FinanceSummarizeRequest(BaseModel):
    articles: list[FinanceArticle]


class FinancePublishRequest(BaseModel):
    summarized_articles: list[SummarizedArticle]
    reservation_data: ReservationData | None