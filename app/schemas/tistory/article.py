from datetime import datetime as dt
from pydantic import BaseModel, model_validator

from app.schemas.enums import ArticleReservationDate


class NewsArticle(BaseModel):
    article: str


class SummarizedArticle(BaseModel):
    title: str
    content: str
    tags: str


class ReservationData(BaseModel):
    type: ArticleReservationDate
    date: str
    time: str | None = None

    @model_validator(mode='after')
    def check_date_not_past(self):
        if self.date < dt.now().strftime('%Y-%m-%d'):
            raise ValueError('예약 날짜가 오늘보다 이전입니다')
        return self