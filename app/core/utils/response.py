from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    data=None,
    status_code: int = status.HTTP_200_OK,
    code: str | None = None
) -> JSONResponse:
    """
    성공 응답을 반환하는 함수

    data 에는 dict 뿐 아니라 Pydantic 모델/모델 리스트/datetime 등이 섞여 있어도 된다.
    jsonable_encoder 가 JSON 호환 형태로 직렬화하므로, 호출부에서 model_dump() 할 필요가 없다.

    Args:
        data: 성공 응답의 데이터. Defaults to None.
        status_code (int): HTTP 상태 코드. Defaults to 200.
        code (str | None): 응답 본문의 "code" 값(업무 코드). 없으면 status_code를 문자열로 사용. Defaults to None.

    Returns:
        JSONResponse: 성공 응답을 포함하는 FastAPI JSONResponse 객체.
    """
    if data is None:
        data = {}

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "code": code if code is not None else str(status_code),
            "data": data
        })
    )


def error_response(
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    code: str | None = None,
    message: str | None = None,
    errors: list | None = None
) -> JSONResponse:
    """
    오류 응답을 반환하는 함수

    Args:
        status_code (int): HTTP 상태 코드. Defaults to 500.
        code (str | None): 응답 본문의 "code" 값(업무 코드). 없으면 status_code를 문자열로 사용. Defaults to None.
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
        status_code=status_code,
        content={
            "code": code if code is not None else str(status_code),
            "message": message,
            "errors": errors
        }
    )