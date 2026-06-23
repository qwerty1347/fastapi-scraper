from enum import Enum


class BlogCategory(str, Enum):
    entertain: str = "entertain"
    finance: str = "finance"
    coding: str = "coding"


class ArticleReservationDate(str, Enum):
    fix: str = "fix"
    random: str = "random"