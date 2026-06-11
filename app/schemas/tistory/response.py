from pydantic import BaseModel


class PostingResponse(BaseModel):
    posted_count: int