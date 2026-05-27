# Browser Manager 설계

Playwright 기반 브라우저 인프라(`app/modules/browser`)와 스크래핑 비즈니스 로직(`app/services`) 분리 가이드.

## 디렉터리 매핑

```
app/
├── modules/
│   └── browser/
│       └── playwright.py        # BrowserManager (인프라)
└── services/
    ├── scraper/                 # 범용 스크래핑 서비스
    └── tistory/                 # 사이트별 비즈니스 로직
        ├── browser.py
        ├── login.py
        └── post.py
```

- **`modules/browser`** — Playwright 생명주기·Context 생성만 담당. 사이트 지식 없음.
- **`services/*`** — 도메인 로직(로그인, 글쓰기, 스크래핑). BrowserManager를 주입받아 사용.

## 인스턴스 모델

- **브라우저는 앱 수명당 1개** — 시작 비용(수백 ms~수초)이 크므로 요청마다 띄우지 않음.
- **Context는 작업/세션당 1개** — 쿠키·세션 격리. 가벼우니 자유롭게 생성·폐기.
- **Page는 단위 작업당 1개** — 사용 후 즉시 close.

| 단위        | 비용 | 격리 | 권장 수명           |
| ----------- | ---- | ---- | ------------------- |
| Browser     | 무거움 | —    | 앱 lifespan         |
| Context     | 가벼움 | 쿠키/스토리지 | 요청 또는 세션 단위 |
| Page        | 매우 가벼움 | DOM | 단위 작업 단위      |

## BrowserManager (`app/modules/browser/playwright.py`)

```python
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright


class BrowserManager:
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self._pw: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        if self._browser is not None:
            return
        self._pw = await async_playwright().start()
        launcher = getattr(self._pw, self.browser_type)
        self._browser = await launcher.launch(headless=self.headless)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._browser = None
        self._pw = None

    @property
    def browser(self) -> Browser:
        if self._browser is None:
            raise RuntimeError("BrowserManager not started. Call start() first.")
        return self._browser

    async def new_context(self, **kwargs) -> BrowserContext:
        return await self.browser.new_context(**kwargs)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()
```

**책임 경계**
- Playwright 시작/종료
- 브라우저 launch 옵션(headless, browser_type 등)
- Context 생성 위임 (`new_context`)

**하지 않는 것**
- 로그인, 페이지 이동, 셀렉터 조작 — 모두 Service의 몫.

## Service 레이어 예시 (`app/services/tistory`)

```python
# app/services/tistory/login.py
from playwright.async_api import Page
from app.modules.browser.playwright import BrowserManager


class TistoryLoginService:
    def __init__(self, browser_manager: BrowserManager):
        self.bm = browser_manager

    async def login(self, user_id: str, password: str) -> dict:
        """로그인 후 storage_state(쿠키)를 반환."""
        context = await self.bm.new_context()
        try:
            page = await context.new_page()
            await page.goto("https://www.tistory.com/auth/login")
            await page.fill("#loginId--1", user_id)
            await page.fill("#password--2", password)
            await page.click("button.btn_login")
            await page.wait_for_url("**/manage")
            return await context.storage_state()
        finally:
            await context.close()
```

```python
# app/services/tistory/post.py
class TistoryPostService:
    def __init__(self, browser_manager: BrowserManager):
        self.bm = browser_manager

    async def write_post(self, storage_state: dict, title: str, html: str) -> str:
        context = await self.bm.new_context(storage_state=storage_state)
        try:
            page = await context.new_page()
            await page.goto("https://blog.tistory.com/manage/newpost/")
            # ... 작성 로직
            return "post_url"
        finally:
            await context.close()
```

**왜 storage_state를 주고받나?** 로그인은 한 번만 하고 결과(쿠키)를 재사용하면 매 요청마다 로그인하는 비용을 피할 수 있음. DB나 캐시에 저장 가능.

## FastAPI 통합

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.modules.browser.playwright import BrowserManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    bm = BrowserManager(headless=True)
    await bm.start()
    app.state.browser_manager = bm
    try:
        yield
    finally:
        await bm.stop()


app = FastAPI(lifespan=lifespan)
```

```python
# app/api/deps.py
from fastapi import Depends, Request
from app.modules.browser.playwright import BrowserManager
from app.services.tistory.login import TistoryLoginService


def get_browser_manager(request: Request) -> BrowserManager:
    return request.app.state.browser_manager


def get_login_service(
    bm: BrowserManager = Depends(get_browser_manager),
) -> TistoryLoginService:
    return TistoryLoginService(bm)
```

```python
# app/api/routes/tistory.py
@router.post("/tistory/login")
async def login(
    req: LoginRequest,
    svc: TistoryLoginService = Depends(get_login_service),
):
    return await svc.login(req.user_id, req.password)
```

## 설계 원칙

1. **인프라는 도메인을 모른다** — BrowserManager에 사이트별 로직(`tistory_login()` 같은 메서드)을 절대 추가하지 않음.
2. **서비스는 Context의 주인** — 서비스가 만들고, 서비스가 닫음. BrowserManager가 Context를 보관하지 않음.
3. **DI로 결합도 낮춤** — 서비스는 `BrowserManager`를 생성자로 주입받음. 테스트 시 mock 교체 가능.
4. **공유 가능한 단일 인스턴스** — `app.state`에 하나만 두고 모든 서비스가 공유.

## 동시성 주의사항

- Playwright Browser는 동시 Context 생성이 가능하지만, **수십 개 이상 동시에 열면 메모리 폭증**. 필요하면 `asyncio.Semaphore`로 동시 Context 수 제한.
- 같은 BrowserManager를 여러 워커가 공유할 때 `start()`가 동시에 호출될 수 있다면 `asyncio.Lock` 추가 고려.

## 확장 포인트

- **세션 풀**: 사이트별 storage_state를 캐시(Redis 등)에 저장해 재사용.
- **다중 브라우저 타입**: chromium/firefox/webkit이 모두 필요하면 `BrowserManager`를 타입별로 여러 인스턴스 생성.
- **프록시·UA 로테이션**: `new_context(proxy=..., user_agent=...)` 인자로 서비스 레벨에서 주입.
