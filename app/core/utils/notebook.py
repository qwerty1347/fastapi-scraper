"""
Jupyter 노트북에서 **Playwright(및 그 외 subprocess 기반 async 라이브러리)** 를
Windows 환경에서도 안전하게 실행하기 위한 헬퍼.

배경
----
- Jupyter는 셀에서 `await ...` 를 바로 쓸 수 있도록 자체 이벤트 루프를 이미 돌리고 있다.
- 그런데 Jupyter가 띄우는 기본 루프는 `SelectorEventLoop` 이고,
  **Windows의 `SelectorEventLoop`는 subprocess 생성을 지원하지 않는다.**
- Playwright는 브라우저를 별도 프로세스로 띄우므로 위 루프에서는 `NotImplementedError`가 난다.

해결 방식
---------
- 노트북 메인 루프는 그대로 두고, **별도의 데몬 스레드에서 `ProactorEventLoop`를 띄워**
  Playwright용 전용 백그라운드 루프로 사용한다.
- `run_async(coro)` 가 호출되면 코루틴을 그 백그라운드 루프로 넘겨 실행하고,
  결과를 호출 셀로 동기적으로 돌려준다 (보기엔 동기처럼 보이지만 내부는 비동기로 동작).
- 이 백그라운드 루프는 노트북 세션 동안 살아 있으므로,
  한 셀에서 만든 Playwright 객체(Browser/Context/Page)를 다음 셀에서 그대로 쓸 수 있다.

사용해야 할 때
-------------
- 노트북에서 **Playwright** 를 호출할 때 (사실상 이게 주된 용도).
- 그 외 Windows에서 `asyncio.subprocess`, 외부 프로세스를 띄우는 async 라이브러리를 다룰 때.

사용하지 않아도 되는 때
-----------------------
- 노트북에서 HTTP 클라이언트(httpx 등), DB, 파일 IO 등 일반 async 호출 → 그냥 셀에서 `await`.
- FastAPI 런타임 같은 서버 코드 → 거기서는 정상 이벤트 루프가 있으므로 그냥 `await`.
- macOS / Linux 의 Playwright → ProactorEventLoop 이슈가 없어 보통 그냥 `await` 로도 동작.

사용 예
-------
    from app.core.utils.notebook import run_async
    from app.modules.browser.playwright import PlaywrightManager
    from app.services.tistory.login import TistoryLoginService

    svc = TistoryLoginService(PlaywrightManager())
    run_async(svc.do_login())     # ← 노트북에서 비동기 Playwright 코드 실행
"""

import asyncio
import sys
import threading
from typing import Coroutine, TypeVar

T = TypeVar("T")

# Windows에서 subprocess 지원 루프를 기본값으로 강제.
# (백그라운드 스레드에서 새로 만드는 루프에 영향을 주기 위함)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class _PlaywrightBackgroundLoop:
    """노트북 세션 동안 살아있는 Playwright 전용 이벤트 루프.

    Jupyter 메인 루프(SelectorEventLoop)와 별개로 데몬 스레드에서 ProactorEventLoop를
    띄워, Windows에서 subprocess 기반 라이브러리(Playwright 등)를 사용 가능하게 한다.

    이 루프는 노트북 세션 전체에 걸쳐 단 하나만 존재한다 → 한 번 만든 Playwright
    Browser/Context/Page 객체를 셀 간에 계속 재사용할 수 있다.
    """

    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # 백그라운드 스레드가 루프를 띄울 때까지 대기 (이후 submit 호출이 안전해진다)
        self._ready.wait()

    def _run(self) -> None:
        # 스레드 내부에서 새 루프 생성·등록 후 영구 실행
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._ready.set()
        self.loop.run_forever()

    def submit(self, coro: Coroutine):
        # 메인 스레드에서 백그라운드 루프로 코루틴을 넘기는 thread-safe 입구
        return asyncio.run_coroutine_threadsafe(coro, self.loop)


# 모듈 전역 싱글턴: 처음 run_async 호출 시 한 번만 생성
_bg: _PlaywrightBackgroundLoop | None = None


def _get_bg() -> _PlaywrightBackgroundLoop:
    global _bg
    if _bg is None:
        _bg = _PlaywrightBackgroundLoop()
    return _bg


def run_async(coro: Coroutine[None, None, T]) -> T:
    """노트북에서 Playwright(또는 subprocess 기반) async 코드를 동기적으로 실행.

    내부적으로는 백그라운드 ProactorEventLoop에 코루틴을 제출하고 결과를 회수한다.
    노트북 셀에서 `result = run_async(some_async())` 식으로 사용한다.

    참고:
    - 모든 호출이 동일한 백그라운드 루프를 공유하므로, 이전 호출로 얻은 Playwright
      객체(Browser/Context/Page)를 다음 호출에서 그대로 넘겨 사용해도 안전하다.
    - FastAPI 런타임에서는 사용하지 말 것. 그쪽은 자체 이벤트 루프가 있으므로
      평범하게 `await ...` 로 호출하면 된다.
    - 일반 async (HTTP/DB/파일 IO 등)은 굳이 이 함수가 필요 없다. 노트북 셀에서
      그냥 `await`로 호출해도 동작한다.
    """
    return _get_bg().submit(coro).result()
