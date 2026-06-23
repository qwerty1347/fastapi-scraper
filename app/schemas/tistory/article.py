from datetime import datetime as dt
from typing import Annotated
from pydantic import BaseModel, Field, model_validator

from app.schemas.enums import ArticleReservationType


class NewsArticle(BaseModel):
    article: Annotated[str, Field(min_length=1)]


class SummarizedArticle(BaseModel):
    title: Annotated[str, Field(min_length=1)]
    content: Annotated[str, Field(min_length=1)]
    tags: Annotated[str, Field(min_length=1)]


class ReservationData(BaseModel):
    type: ArticleReservationType
    date: Annotated[str, Field(pattern=r'^\d{4}-\d{2}-\d{2}$')]
    time: Annotated[str, Field(pattern=r'^\d{2}:\d{2}$')] | None = None

    @model_validator(mode='after')
    def check_date_not_past(self):
        if self.date < dt.now().strftime('%Y-%m-%d'):
            raise ValueError('예약 날짜가 오늘보다 이전입니다')
        return self