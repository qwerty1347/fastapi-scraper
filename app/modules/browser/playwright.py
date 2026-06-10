from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright


class PlaywrightManager:
    def __init__(self, headless=False):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.headless: bool = headless


    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)


    async def close(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.browser = None
        self.playwright = None


    async def create_context(self, storage_state: str | None = None) -> BrowserContext:
        return await self.browser.new_context(storage_state=storage_state)