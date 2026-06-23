from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.enums import BlogCategory
from app.schemas.tistory.article import NewsArticle, ReservationData, SummarizedArticle


class TistorySummarizeRequest(BaseModel):
    articles: Annotated[list[NewsArticle], Field(min_length=1)]


class TistoryPublishRequest(BaseModel):
    blog_category: BlogCategory
    summarized_articles: Annotated[list[SummarizedArticle], Field(min_length=1)]
    reservation_data: ReservationData | None = None