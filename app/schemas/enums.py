from enum import Enum


class BlogCategory(str, Enum):
    entertain = "entertain"
    finance = "finance"
    coding = "coding"


class ArticleReservationType(str, Enum):
    fix = "fix"
    random = "random"