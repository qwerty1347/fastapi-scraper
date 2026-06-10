from enum import Enum


class ArticleReservationDate(str, Enum):
    fix: str = "fix"
    random: str = "random"