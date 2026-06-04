from datetime import datetime

from app.core.config import STORAGE_PATH
from app.core.utils.file import ensure_directory


def save_log(message: str, category: str | None = None) -> None:
    """카테고리별 일자 파일에 메시지 한 줄 추가.

    파일 경로:
        - category 있음: storage/logs/{category}/{YYYY-MM-DD}.log
        - category 없음: storage/logs/{YYYY-MM-DD}.log
    줄 형식 : HH:MM:SS message
    파일 없으면 생성, 있으면 끝에 한 줄 추가.

    예:
        save_log(article_page.url)
        save_log(article_page.url, 'tistory')
        save_log(f'발행 성공: {title}', 'tistory')
        save_log(f'요약 완료 | 입력 {len(text)}자', 'llm')
    """
    now = datetime.now()
    log_dir = STORAGE_PATH / "logs"

    if category is not None:
        log_dir = log_dir / category

    ensure_directory(log_dir)

    log_file = log_dir / f"{now:%Y-%m-%d}.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{now:%H:%M:%S} {message}\n")