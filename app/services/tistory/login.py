import time

from playwright.async_api import BrowserContext, Page

from app.core.config import TISTORY_STORAGE
from app.core.log import logger
from app.core.utils.error import exception_format
from app.core.utils.file import ensure_directory
from app.modules.browser.playwright import PlaywrightManager


class TistoryLoginService:
    """
    티스토리 카카오 로그인을 자동화하고 세션을 파일로 보관하는 서비스.
    """

    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self.context: BrowserContext | None = None
        self.page: Page | None = None


    async def open_login_page(self) -> Page:
        """브라우저를 띄우고 티스토리 메인 페이지를 연다."""
        await self.pm.start(headless=False)
        self.context = await self.pm.create_context()
        self.page = await self.context.new_page()
        await self.page.goto("https://www.tistory.com", wait_until="domcontentloaded")
        return self.page


    async def click_kakao_login(self):
        """티스토리 메인 → 카카오 로그인 페이지로 이동"""
        await self.page.get_by_role("link", name="카카오계정으로 시작하기").click()
        await self.page.get_by_role("link", name="카카오계정으로 로그인").click()


    async def save_session(self):
        """현재 컨텍스트의 쿠키·로컬스토리지를 JSON 파일로 저장"""
        ensure_directory(TISTORY_STORAGE)
        tistory_context = TISTORY_STORAGE / "browser_context.json"
        await self.context.storage_state(path=tistory_context)


    async def do_login(self):
        """로그인 전체 플로우를 담당 (페이지 열기 → 카카오 이동 → 사람 로그인 대기 → 세션 저장)"""
        try:
            await self.open_login_page()

            # main frame URL이 바뀔 때마다 출력
            def on_nav(frame):
                if frame == self.page.main_frame:
                    print(f"  -> navigated: {frame.url}")
            self.page.on("framenavigated", on_nav)

            t0 = time.time()

            # expect_navigation 컨텍스트 안에서 클릭해 "카카오 도메인으로 이동"까지 같이 기다린다.
            async with self.page.expect_navigation(
                url="**/accounts.kakao.com/**",
                timeout=15_000,
            ):
                await self.click_kakao_login()

            print(f"[{time.time()-t0:.1f}s] 로그인 진행하세요...")

            # 카카오에서 ID/PW 입력 → 인증 완료 → tistory 도메인으로 리다이렉트.
            # 도착 URL이 케이스마다 다르므로(/, /auth/kakao/redirect?code=..., 서브도메인 등 "tistory.com 포함 && 카카오 도메인 아님" 조건으로 유연하게 매칭한다.
            # 단순 "tistory.com in url"만 쓰면 카카오 URL의 redirect_uri 쿼리에 박힌 tistory.com 문자열에도 매칭돼버려서 카카오 두 도메인을 명시적으로 배제.
            await self.page.wait_for_url(
                lambda url: "tistory.com" in url
                    and "accounts.kakao.com" not in url
                    and "kauth.kakao.com" not in url,
                timeout=300_000,  # 5분
            )

            print(f"[{time.time()-t0:.1f}s] 복귀 완료, 현재 url = {self.page.url}")

            await self.save_session()
            print("done")

        except Exception as e:
            print(exception_format(e))
            print(f"최종 url = {self.page.url if self.page else 'no page'}")

        finally:
            # await self.page.pause()
            await self.pm.close()