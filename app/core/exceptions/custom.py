class BusinessException(Exception):
    def __init__(self, code: int, message: str, errors: list | None = None):
        super().__init__(message)   # str(e) 가 message 를 반환하도록 부모에 전달
        self.code = code
        self.message = message
        self.errors = errors


class TistorySessionExpiredException(BusinessException):
    """카카오 OAuth 세션이 만료되었거나 storage_state 파일이 올바르지 않을 때 발생."""

    def __init__(self):
        super().__init__(
            code=401,
            message=(
                "티스토리 로그인 세션이 만료되었습니다. "
                "storage/tistory/browser_context.json 을 갱신하세요."
            ),
        )