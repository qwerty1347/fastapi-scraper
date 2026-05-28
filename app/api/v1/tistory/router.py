from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies.tistory import get_tistory_post_service
from app.core.utils.response import success_response
from app.schemas.common import BaseResponse
from app.services.tistory.origin_post import TistoryPostService


router = APIRouter(prefix="/tistory", tags=["tistory"])

@router.get('/', response_model=BaseResponse[dict])
def index() -> JSONResponse:
    return success_response()