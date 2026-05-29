import asyncio

from playwright.async_api import BrowserContext, Page

from app.core.config import TISTORY_STORAGE
from app.core.utils.error import exception_format
from app.modules.browser.playwright import PlaywrightManager


class TistoryPostService:
    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.post_page: Page | None = None

        """
        todo: 글쓰기
        ✅1 context 불러와 로그인
        ✅2 티스토리 페이지 이동
        ✅3 글쓰기 버튼 클릭
        ✅4 글쓰기 시작
        ✅5 발행
        6 브라우저 종료

        todo: 스크래핑
        ✅1 스크래핑 사이트 접속
        ✅2 스크래핑
        ✅3 스크래핑 텍스트 가공

        todo: LLM
        1 스크래핑 텍스트를 통해 llm 요청
        2 글쓰기 내용에 연동
        """


    async def do_login(self):
        await self.pm.start(headless=False)
        tistory_context = str(TISTORY_STORAGE / "browser_context.json")
        self.context = await self.pm.create_context(storage_state=tistory_context)
        self.page = await self.context.new_page()
        await self.page.goto("https://www.tistory.com", wait_until="domcontentloaded")


    async def click_post_page(self):
        self.page.once('dialog', lambda dialog: asyncio.create_task(dialog.dismiss()))
        async with self.context.expect_page() as new_page_info:
            await self.page.get_by_role('link', name='글쓰기').click()
        self.post_page = await new_page_info.value


    async def write_posting(self):
        await self.post_page.locator('#post-title-inp').type('제목입니당...', delay=30)
        await self.post_page.wait_for_selector('#editor-tistory_ifr')
        editor_iframe = self.post_page.frame_locator('#editor-tistory_ifr')
        await editor_iframe.locator('#tinymce').type('본문 내용 입니당...', delay=30)
        await self.post_page.get_by_role('button', name='완료').click()

        # todo: 태그 추가


    async def publish_posting(self):
        await self.post_page.locator('input[name="basicSet"][value="20"]').check()  # 기본
        await self.post_page.get_by_role('button', name='현재').click()  # 발행일
        await self.post_page.get_by_role('button', name='공개 발행').click()  # 공개발행

        # todo: 홈주제 추가


    async def do_post(self):
        try:
            await self.do_login()
            await self.click_post_page()
            await self.write_posting()
            await self.publish_posting()

        except Exception as e:
            print(exception_format(e))

        finally:
            # self.post_page.pause()
            await self.pm.close()