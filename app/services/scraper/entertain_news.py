import random

from app.core.utils.error import exception_format
from app.core.utils.log import save_log
from app.modules.browser.playwright import PlaywrightManager
from app.schemas.tistory.article import EntertainmentArticle
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


    async def do_scraping(self) -> list[EntertainmentArticle]:
        try:
            await self.open_scraping_page(ENTERTAIN_NEWS_URL)
            print("* 아티클 스크래핑")
            pickecd_newslink = await self.scrap_news_href()

            print(pickecd_newslink)

            """ articles = []
            for href in pickecd_newslink:
                await self.page.goto(href, wait_until="domcontentloaded")
                save_log(href, 'tistory/entertain_news')
                article = await self.scrap_article()
                articles.append(article) """

            # ! 하드코딩
            articles = [
                {'article': '[텐아시아=홍길동 기자] 가수 에일리가 최근 SNS에서 불거진 임신설에 사실이 아니라는 입장을 밝혔다./제공사진 가수 에일리가 최근 SNS에서 불거진 임신설에 사실이 아니라는 입장을 밝혔다. 19일 소속사 A2Z엔터테인먼트 관계자는 "에일리의 임신은 사실이 아니"라며 "좋은 소식이 생기면 전해드리겠다"고 밝혔다. 앞서 에일리는 최근 한 지역 축제 무대에 올라 히트곡 \'U&I\'를 비롯한 여러 곡을 선보였다. 이후 공연 영상과 사진이 온라인 커뮤니티와 SNS를 중심으로 확산하면서 예상치 못한 임신설에 휩싸였다. 가수 에일리가 최근 SNS에서 불거진 임신설에 사실이 아니라는 입장을 밝혔다./사진=SNS 갈무리 일부 누리꾼은 에일리가 허리 라인이 드러나지 않는 넉넉한 핏의 원피스를 착용한 점과 한층 편안해 보이는 스타일링에 주목하며 임신 가능성을 제기했다. 현재 에일리가 남편 최시훈과 함께 2세를 준비하며 시험관 시술에 도전 중인 사실이 알려진 만큼 다양한 추측이 이어진 것으로 보인다. 에일리의 소속사는 이 같은 소문에 선을 그으며 임신설을 부인했다. 에일리와 최시훈은 지난해 4월 결혼식을 올렸다. 두 사람은 유튜브 콘텐츠 등을 통해 시험관 시술 과정과 2세 준비 과정을 공개하며 많은 응원을 받고 있다.'}, {'article': '[서울=뉴스] 정선희. (사진=유튜브 채널 \'들어볼까\' 캡처) 2026.04.08. photo@test.com *재판매 및 DB 금지 [서울=뉴스] 테스터 기자 = 홍진경이 절친한 동료인 정선희의 과거 아픔을 언급했다. 18일 채널 \'공부왕찐천재 홍진경\'에는 \'30년 찐친 호자언니에게 털어놓은 홍진경 요즘 심경 (+정선희)\'이라는 제목의 영상이 게재됐다. 이날 홍진경은 정선희에 대해 "언니가 너무 큰 아픔을 겪었는데 이상하게 사람들은 아픔을 겪은 언니를 공격하더라"라고 했다. 그는 "언니가 욕먹을 일이 아닌데 언니는 자기 인생도 갑자기 무너졌는데 거기다가 알 수 없는 욕까지 먹으니까"라며 "그냥 사람이 달팽이가 자기 집 안에 들어가듯이 그냥 딱 들어가더라"라고 했다. 그러면서 "내가 어떡하든 꺼낼 수가 없었다"라고 했다. 정선희는 "그래도 수시로 꺼내러 왔다"라고 답했다. 2008년 배우 안재환과 최진실의 연이은 사망 이후, 아내이자 동료였던 정선희는 대중의 악성 댓글과 루머로 인해 끔찍한 비난과 마녀사냥에 시달린 바 있다. 안재환이 거액의 사채로 인해 사망하자, 일부 누리꾼은 정선희가 \'실종 신고를 늦게 했다\', \'돈 문제에 관여했다\'는 근거 없는 루머를 퍼뜨리며 고인의 죽음을 정선희의 탓으로 몰았다.'}
            ]
            return [EntertainmentArticle.model_validate(item) for item in articles]


        except Exception as e:
            print(exception_format(e))
            raise e

        finally:
            await self.pm.close()