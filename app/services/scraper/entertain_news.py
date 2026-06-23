import random

from app.core.utils.error import exception_format
from app.core.utils.log import save_log
from app.modules.browser.playwright import PlaywrightManager
from app.schemas.tistory.article import NewsArticle
from app.services.scraper.base import BaseScraperService


ENTERTAIN_NEWS_URL= "https://m.entertain.naver.com/ranking"


class EntNewsScrapService(BaseScraperService):
    def __init__(self, playwright_manager: PlaywrightManager):
        super().__init__(playwright_manager)


    async def scrap_news_href(self):
        newslist = self.page.locator('li[class*="NewsItem_news_item__fhEmd"] a')
        hrefs = await newslist.evaluate_all("els => els.map(a => a.href)")
        pickecd_newslink = random.sample(hrefs, k=2)
        return pickecd_newslink


    async def scrap_article(self) -> dict[str, str]:
        content = await self.page.locator('._article_content').inner_text()
        article = " ".join(content.split())
        return {'article': article}


    async def do_scraping(self) -> list[NewsArticle]:
        try:
            print("* 아티클 스크래핑")
            await self.open_scraping_page(ENTERTAIN_NEWS_URL)
            pickecd_newslink = await self.scrap_news_href()

            articles = []
            for href in pickecd_newslink:
                await self.page.goto(href, wait_until="domcontentloaded")
                save_log(href, 'tistory/entertain_news')
                article = await self.scrap_article()
                articles.append(article)

            return [NewsArticle.model_validate(item) for item in articles]


        except Exception as e:
            print(exception_format(e))
            raise e

        finally:
            await self.pm.close()