from abc import ABC, abstractmethod
from dataclasses import dataclass

from playwright.async_api import BrowserContext, Page

from app.modules.browser.playwright import PlaywrightManager


class BaseScraperService(ABC):
    def __init__(self, playwright_manager):
        self.pm: PlaywrightManager = playwright_manager
        self.page: Page | None = None
        self.context: BrowserContext | None = None


    async def open_scraping_page(self, url: str):
        await self.pm.start()
        self.context = await self.pm.create_context()
        self.page = await self.context.new_page()
        await self.page.goto(url, wait_until='domcontentloaded')


    @abstractmethod
    async def scrap_article(self):
        pass


    @abstractmethod
    async def do_scraping(self):
        pass