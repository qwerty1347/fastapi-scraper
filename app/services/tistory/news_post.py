import asyncio
import random

from datetime import datetime as dt
from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from app.core.config import TISTORY_STORAGE
from app.core.exceptions.custom import TistorySessionExpiredException
from app.core.logger import logger
from app.core.utils.error import exception_format
from app.modules.browser.playwright import PlaywrightManager
from app.schemas.tistory.article import ReservationData, SummarizedArticle


class TistoryPostService:
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
    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.post_page: Page | None = None


    async def do_login(self):
        await self.pm.start()
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


    def handle_reservation_data(self, reservation_data: ReservationData) -> dict[str, str]:
        date = reservation_data.date

        match (reservation_data.type):
            case ('fix'):
                time = reservation_data.time.split(':')
                hour = time[0]
                minutes = time[1]
            case ('random'):
                hour = f"{random.randint(9, 18):02d}"
                minutes = f"{random.randint(0, 59):02d}"

        return {'date': date, 'hour': hour, 'minutes': minutes}


    async def click_post_page(self):
        self.page.once('dialog', lambda d: asyncio.create_task(d.dismiss()))
        async with self.context.expect_page() as new_page_info:
            await self.page.get_by_role('link', name='글쓰기').click()
        self.post_page = await new_page_info.value

        # 새 탭에서 발생하는 모든 dialog를 메시지 기반으로 자동 처리
        self.post_page.on('dialog', self._handle_dialog)


    async def write_posting(self, article: SummarizedArticle):
        # 1) 마크다운 모드로 전환 (confirm은 _handle_dialog가 자동 처리)
        await self.post_page.locator('#editor-mode-layer-btn-open').click()
        await self.post_page.wait_for_selector('#editor-mode-markdown-text')
        await self.post_page.locator('#editor-mode-markdown-text').click()

        # 2) 제목
        await self.post_page.locator('#post-title-inp').fill(article.title)

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
        """, article.content)

        # 추가 안전망: keyboard로 글자 하나 더 입력 후 backspace
        # → 티스토리가 사용자 입력으로 인식하여 폼 상태 갱신
        await self.post_page.locator('.CodeMirror.cm-s-tistory-markdown').click()
        await self.post_page.keyboard.press('End')
        await self.post_page.keyboard.type(' ')
        await self.post_page.keyboard.press('Backspace')

        # 4) 태그
        await self.post_page.wait_for_selector('input[name="tagText"]')
        tag_text = self.post_page.locator('input[name="tagText"]')
        tags = [t.strip() for t in article.tags.split('||') if t.strip()][:6]
        for tag in tags:
            await tag_text.fill(tag)
            await tag_text.press('Enter')

        # 5) 완료
        await self.post_page.locator('#publish-layer-btn').click()

        # todo: 카테고리 추가


    async def select_reservation_date(self, target_date: str):
        """캘린더를 열어 target_date('YYYY-MM-DD')를 실제로 클릭해 선택.

        button.btn_reserve 의 textContent 만 바꾸면 표시는 되지만 Tistory 내부
        상태가 갱신되지 않아 발행 시 무시되므로, 반드시 캘린더 UI 클릭으로 선택해야 함.

        티스토리 캘린더 DOM:
            .layer_info > .inner_layer > .box_calendar
                ├ .info_date
                │   ├ strong.txt_calendar  (예: "2026년 6월")
                │   ├ button.btn_prev      (disabled 가능 = 과거 이동 불가)
                │   └ button.btn_next
                └ .wrab_tbl > table.tbl_calendar  (날짜 셀)
        """
        target = dt.strptime(target_date, "%Y-%m-%d")

        # 1) 캘린더 열기
        await self.post_page.locator('button.btn_reserve').click()
        await asyncio.sleep(0.3)

        # 2) 헤더가 target 의 연-월이 될 때까지 이전/다음 클릭
        max_iters = abs((target.year - dt.now().year)) * 12 + 12
        for _ in range(max_iters):
            # 캘린더 popup 내부 헤더만 정확히 지정 (본문 텍스트와 충돌 방지)
            header_text = await self.post_page.locator(
                '.box_calendar strong.txt_calendar'
            ).inner_text(timeout=2000)

            # "2026년 6월" 파싱
            parts = header_text.replace('년', '-').replace('월', '').split('-')
            cur = dt(int(parts[0].strip()), int(parts[1].strip()), 1)
            tgt_month = dt(target.year, target.month, 1)

            if cur == tgt_month:
                break
            elif cur < tgt_month:
                await self.post_page.locator('.box_calendar button.btn_next').click()
            else:
                await self.post_page.locator('.box_calendar button.btn_prev').click()
            await asyncio.sleep(0.15)

        # 3) 해당 일자 클릭 (캘린더 테이블 내부로 한정 → 본문/태그와 충돌 방지)
        await self.post_page.locator(
            f'.box_calendar table.tbl_calendar :text("{target.day}")'
        ).first.click()


    async def publish_posting(self, reservation_data: ReservationData | None = None):
        # 1) 기본 (공개)
        await self.post_page.locator('input[name="basicSet"][value="20"]').check()

        # 2) 발행일 (현재/예약)
        if reservation_data is None:
            await self.post_page.get_by_role('button', name='현재').click()
        else:
            await self.post_page.get_by_role('button', name='예약').click()
            datetime = self.handle_reservation_data(reservation_data)

            # 캘린더 UI로 날짜 실제 선택
            await self.select_reservation_date(datetime['date'])

            # 시·분 — fill 후 Tab 으로 blur 트리거
            await self.post_page.locator('#dateHour').fill(datetime['hour'])
            await self.post_page.locator('#dateHour').press('Tab')
            await self.post_page.locator('#dateMinute').fill(datetime['minutes'])
            await self.post_page.locator('#dateMinute').press('Tab')

        # 3) 공개 발행
        await self.post_page.get_by_role('button', name='공개 발행').click()  # 공개발행

        # todo: 대표이미지, 홈주제 추가


    async def do_posting(self, summarized_articles: list[SummarizedArticle], reservation_data: ReservationData | None = None) -> dict[str, int]:
        try:
            await self.do_login()
            print("* 로그인")

            for index, article in enumerate(summarized_articles):
                await self.click_post_page()
                print(f"* {index + 1}번째 글쓰기")
                await self.write_posting(article)
                print(f"* {index + 1}번째 글발행")
                await self.publish_posting(reservation_data)
                await asyncio.sleep(random.uniform(1, 2))

            return {
                'posted': len(summarized_articles),
            }

        except PlaywrightTimeoutError as e:
            print("* 로그인 실패")
            print(exception_format(e))
            raise TistorySessionExpiredException()

        except Exception as e:
            print(exception_format(e))
            raise

        finally:
            # await self.page.pause()
            # await self.post_page.pause()
            await self.pm.close()