import logging
import sys


__all__ = ["logger", "setup_logging"]

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d\n%(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )


# 어디서든 import해서 쓸 수 있는 전역 logger.
# 사용: from app.core.logger import logger
# formatter의 %(pathname)s:%(lineno)d 가 호출된 위치를 자동으로 캡처하므로
# 매 파일마다 getLogger(__name__) 할 필요 없음.
logger: logging.Logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # stderr 사용: Jupyter 노트북에서 백그라운드 스레드(run_async)의 출력도 잡힘.
    # stdout은 메인 스레드 출력만 셀에 표시되는 경향이 있어 노트북 호환성을 위해 stderr 선택.
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(_handler)
    logger.propagate = False  # 루트 logger로 전파 안 함 (중복 출력 방지)
