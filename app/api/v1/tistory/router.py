from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.utils.response import success_response


router = APIRouter(prefix="/tistory", tags=["tistory"])

@router.get('/')
def index() -> JSONResponse:
    return success_response()