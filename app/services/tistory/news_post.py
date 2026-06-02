import asyncio
import logging
import random

from playwright.async_api import BrowserContext, Page

from app.core.config import TISTORY_STORAGE
from app.core.utils.error import exception_format
from app.modules.browser.playwright import PlaywrightManager


logger = logging.getLogger(__name__)

class TistoryNewsPostService:
    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.post_page: Page | None = None

        """
        * 글쓰기
        ✅1 context 불러와 로그인
        ✅2 티스토리 페이지 이동
        ✅3 글쓰기 버튼 클릭
        ✅4 글쓰기 시작
        ✅5 발행
        ✅6 브라우저 종료

        * LLM
        ✅1 스크래핑된 아티클 llm 요청
        ✅2 llm 응답 글쓰기 내용에 연동
        """


    async def do_login(self):
        await self.pm.start(headless=False)
        tistory_context = str(TISTORY_STORAGE / "browser_context.json")
        self.context = await self.pm.create_context(storage_state=tistory_context)
        self.page = await self.context.new_page()
        await self.page.goto("https://www.tistory.com", wait_until="domcontentloaded")


    def _handle_dialog(self, dialog):
        """
        페이지의 dialog confirm을 메시지 보고 처리하는 함수 (accept: 확인, dismiss: 취소)
        """
        msg = ' '.join(dialog.message[:60].split())
        logger.info(f"dialog: {dialog.type} | {msg}")

        if "이어서 작성" in dialog.message:
            asyncio.create_task(dialog.dismiss())
        else:
            asyncio.create_task(dialog.accept())


    async def click_post_page(self):
        self.page.once('dialog', lambda d: asyncio.create_task(d.dismiss()))
        async with self.context.expect_page() as new_page_info:
            await self.page.get_by_role('link', name='글쓰기').click()
        self.post_page = await new_page_info.value

        # 새 탭에서 발생하는 모든 dialog를 메시지 기반으로 자동 처리
        self.post_page.on('dialog', self._handle_dialog)


    async def write_posting(self, article: dict[str, str]):
        # 1) 마크다운 모드로 전환 (confirm은 _handle_dialog가 자동 처리)
        await self.post_page.locator('#editor-mode-layer-btn-open').click()
        await self.post_page.wait_for_selector('#editor-mode-markdown-text')
        await self.post_page.locator('#editor-mode-markdown-text').click()

        # 2) 제목
        await self.post_page.locator('#post-title-inp').fill(article['title'])

        # 3) 본문 — 마크다운 모드 CodeMirror에 입력
        # setValue만으로는 티스토리가 변경 감지를 못 해서 폼 저장 시 빈 본문으로 처리됨.
        # 따라서 setValue로 즉시 값 세팅 후, CodeMirror change 이벤트를 명시적으로 트리거.
        await self.post_page.wait_for_selector('.CodeMirror.cm-s-tistory-markdown')
        await self.post_page.evaluate("""
            (text) => {
                const cms = document.querySelectorAll('.CodeMirror');
                for (const cm of cms) {
                    if (cm.offsetParent !== null && cm.CodeMirror) {
                        const editor = cm.CodeMirror;
                        editor.setValue(text);
                        editor.save();
                        editor.refresh();
                        editor.focus();

                        // CodeMirror change 이벤트 명시적 발생 (티스토리가 변경 감지하도록)
                        const ta = editor.getTextArea && editor.getTextArea();
                        if (ta) {
                            ta.dispatchEvent(new Event('input', { bubbles: true }));
                            ta.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        return;
                    }
                }
            }
        """, article['content'])

        # 추가 안전망: keyboard로 글자 하나 더 입력 후 backspace
        # → 티스토리가 사용자 입력으로 인식하여 폼 상태 갱신
        await self.post_page.locator('.CodeMirror.cm-s-tistory-markdown').click()
        await self.post_page.keyboard.press('End')
        await self.post_page.keyboard.type(' ')
        await self.post_page.keyboard.press('Backspace')

        # 4) 완료
        await self.post_page.get_by_role('button', name='완료').click()

        # 5) 태그
        await self.post_page.wait_for_selector('input[name="tagText"]')
        tag_text = self.post_page.locator('input[name="tagText"]')
        tags = [t.strip() for t in article['tags'].split('||') if t.strip()][:6]
        for tag in tags:
            await tag_text.fill(tag)
            await tag_text.press('Enter')


    async def publish_posting(self):
        await self.post_page.locator('input[name="basicSet"][value="20"]').check()  # 기본
        await self.post_page.get_by_role('button', name='현재').click()  # 발행일
        await self.post_page.get_by_role('button', name='공개 발행').click()  # 공개발행

        # todo: 홈주제 추가


    async def do_posting(self, summarized_article: list[dict[str, str]]):
        try:
            await self.do_login()

            for article in summarized_article:
                print("* 글쓰기 버튼 클릭 *")
                await self.click_post_page()
                print("* 글쓰기 *")
                await self.write_posting(article)
                print("* 글발행 *")
                await self.publish_posting()
                await asyncio.sleep(random.uniform(4, 8))

        except Exception as e:
            print(exception_format(e))

        finally:
            # await self.post_page.pause()
            await self.pm.close()