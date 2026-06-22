from pydantic import BaseModel

from app.schemas.enums import BlogCategory
from app.schemas.tistory.article import NewsArticle, ReservationData, SummarizedArticle


class TistorySummarizeRequest(BaseModel):
    articles: list[NewsArticle]


class TistoryPublishRequest(BaseModel):
    blog_category: BlogCategory
    summarized_articles: list[SummarizedArticle]
    reservation_data: ReservationData | None = None