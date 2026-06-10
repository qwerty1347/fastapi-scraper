from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data=None, code: int = status.HTTP_200_OK) -> JSONResponse:
    """
    성공 응답을 반환하는 함수

    data 에는 dict 뿐 아니라 Pydantic 모델/모델 리스트/datetime 등이 섞여 있어도 된다.
    jsonable_encoder 가 JSON 호환 형태로 직렬화하므로, 호출부에서 model_dump() 할 필요가 없다.

    Args:
        data: 성공 응답의 데이터. Defaults to None.
        code (int): 성공 응답의 상태 코드. Defaults to 200.

    Returns:
        JSONResponse: 성공 응답을 포함하는 FastAPI JSONResponse 객체.
    """
    if data is None:
        data = {}

    return JSONResponse(
        status_code=code,
        content=jsonable_encoder({
            "code": str(code),
            "data": data
        })
    )


def error_response(code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, message: str | None = None, errors: list | None = None) -> JSONResponse:
    """
    오류 응답을 반환하는 함수

    Args:
        code (int): 에러 응답의 상태 코드. Defaults to 500.
        message (str | None): 에러 응답의 메시지. Defaults to None.
        errors (list | None): 에러 정보. Defaults to None.

    Returns:
        JSONResponse: 에러 응답을 포함하는 FastAPI JSONResponse 객체.
    """
    if message is None:
        message = "Internal Server Error"

    if not errors:
        errors = []

    return JSONResponse(
        status_code=code,
        content={
            "code": str(code),
            "message": message,
            "errors": errors
        }
    )