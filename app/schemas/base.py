from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: str
    data: T