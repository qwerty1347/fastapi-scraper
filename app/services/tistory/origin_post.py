import asyncio
import logging

from pathlib import Path
from playwright.async_api import BrowserContext, Page

from app.services.tistory.browser import TistoryBrowserService


logger = logging.getLogger(__name__)

class TistoryPostService:
    def __init__(self, tistory_browser_service: TistoryBrowserService, tistory_context: Path):
        self.tistory_browser_service = tistory_browser_service
        self.tistory_context = tistory_context


    async def do_post(self):
        context = await self.set_context()
        page = await self.open_main_page(context)
        new_page = await self.open_post_page(context, page)
        await self.write_post(new_page)
        await self.publish_post(new_page)
        await self.tistory_browser_service.close_browser()


    async def set_context(self) -> BrowserContext:
        logger.info('set context')
        await self.tistory_browser_service.init_browser(headless=True)
        return await self.tistory_browser_service.load_context(self.tistory_context)


    async def open_main_page(self, context: BrowserContext) -> Page:
        logger.info('open main page')
        page = await context.new_page()
        await page.goto("https://www.tistory.com", wait_until="domcontentloaded")
        page.once('dialog', lambda dialog: asyncio.create_task(dialog.dismiss()))

        return page


    async def open_post_page(self, context: BrowserContext, page: Page) -> Page:
        logger.info('open post page')
        async with context.expect_page() as new_page_info:
            await page.get_by_role('link', name='글쓰기').click()
        post_page = await new_page_info.value

        return post_page


    async def write_post(self, page: Page):
        logger.info('write post')
        await page.locator('#post-title-inp').type('제목입니당...', delay=30)
        frame = page.frame_locator('#editor-tistory_ifr')
        await frame.locator('#tinymce').type('본문 내용 입니당...', delay=30)


    async def publish_post(self, page: Page):
        logger.info('publish post')
        await page.get_by_role('button', name='완료').click()
        await page.locator('input[name="basicSet"][value="20"]').check()
        await page.get_by_role('button', name='현재').click()
        await page.get_by_role('button', name='공개 발행').click()