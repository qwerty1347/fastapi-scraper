from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.log import logger
from app.core.utils.response import success_response
from app.schemas.common import BaseResponse


router = APIRouter(prefix="/scraper", tags=["scraper"])

@router.get('/', response_model=BaseResponse[dict])
def index() -> JSONResponse:
    return success_response()