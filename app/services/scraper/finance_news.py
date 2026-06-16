import random

from playwright.async_api import Locator, Page

from app.core.utils.error import exception_format
from app.core.utils.log import save_log
from app.modules.browser.playwright import PlaywrightManager
from app.schemas.tistory.article import FinanceArticle


FINANCE_NEWS_URL = 'https://finance.naver.com/news/news_list.naver?mode=RANK'

class FinanceNewsScrapService:
    """
    * 스크래핑
    ✅1 스크래핑 사이트 접속
    ✅2 스크래핑
    ✅3 스크래핑 아티클 가공
    """

    def __init__(self, playwright_manager: PlaywrightManager):
        self.pm = playwright_manager
        self.page: Page | None = None


    async def open_finance_news_page(self):
        await self.pm.start()
        self.context = await self.pm.create_context()
        self.page = await self.context.new_page()
        await self.page.goto(FINANCE_NEWS_URL, wait_until='domcontentloaded')


    async def scrap_newslist(self) -> list[Locator]:
        newslist = await self.page.locator("div.hotNewsList ul.simpleNewsList > li").all()
        picked_newslist = random.sample(newslist, k=5)
        return picked_newslist


    async def click_article(self, li: Locator) -> Page:
        async with self.context.expect_page() as new_page_info:
            await li.locator("a").click()
        return await new_page_info.value


    async def scrap_article(self, article_page: Page) -> dict:
        content = await article_page.locator("article#dic_area").text_content()
        article = " ".join(content.split())
        return {'article': article}


    async def do_scraping(self) -> list[FinanceArticle]:
        try:
            await self.open_finance_news_page()
            print("* 아티클 스크래핑")
            picked_newslist = await self.scrap_newslist()

            articles = []
            for news in picked_newslist:
                article_page = await self.click_article(news)
                await article_page.wait_for_load_state('domcontentloaded')
                save_log(article_page.url, 'tistory/finance_news')
                article = await self.scrap_article(article_page)
                articles.append(article)
                await article_page.close()

            # ! 하드코딩
            """ articles = [
                {'article': '\'정의선 로봇\' 기대하는 투심…삼전닉스 다음은 \'현대차 ETF\'삼성자산운용, 다음달 9일 현대차 ETF 출시현대차 투자하는 채권혼합형 ETF도 상장 앞둬증권가, 현대차 목표주가 줄줄이 높여잡아 현대자동차그룹이 양재 사옥을 \'임직원 모두들 위한 광장\'으로 새롭게 조성한 지난 14일 서울 서초구 양재 사옥에서 열린 임직원 대상 로비 오프닝 기념식에서 정의선 회장이 입장하고 있다. 사진=김범준 기자국내 자산운용사들이 잇따라 현대자동차그룹을 담은 상장지수펀드(ETF) 출시에 나서고 있다. 휴머노이드 로봇과 피지컬 인공지능(AI) 시장에서 존재감이 커지자 현대차를 완성차 기업이 아닌 AI 플랫폼 기업으로 바라보고 투자 상품을 출시했다는 분석이다. 증권가는 현대차가 피지컬 AI 산업의 핵심 플레이어로 부상하고 있다며 목표주가를 줄줄이 상향 조정했다.29일 금융투자업계에 따르면 삼성자산운용은 다음달 9일 \'KODEX 현대차로보틱스밸류체인TOP3플러스\'를 출시한다. 이 상품은 현대차와 기아, 현대모비스 등 그룹의 로보틱스 밸류체인과 관련성이 높은 종목 10곳에 투자한다. 엔비디아와 구글처럼 현대차와 협력하는 해외 기업 주식도 들어간다. 보스턴다이내믹스의 휴머노이드 로봇 \'아틀라스\'에 현대차 로고가 처음으로 부착됐다. / 사진=보스턴다이내믹스 유튜브 영상 캡처지난 12일 선보인 KB자산운용의 \'RISE 현대차고정피지컬AI\'는 상장 후 2주 만에 순자산총액(AUM)이 3583억원으로 불어났다. 포트폴리오의 25%는 현대차를 고정 투자하고 나머지 75%는 로보틱스·자율주행·공장자동화 등 관련 기업 14곳을 담는 상품으로, 개인 투자자가 상장 이후 2654억원어치를 순매수했다.현대차에 투자하는 채권혼합형 ETF도 상장을 앞두고 있다. 우리자산운용은 \'WON 삼성전자현대차채권혼합50\' ETF를 다음달 2일 선보인다. 삼성전자와 현대차에 각각 25%씩 투자하고, 나머지 50%는 단기채권에 투자하는 상품이다. 총보수는 0.18%다. 우리자산운용은 "메모리에 쏠린 주식형 비중을 수출 주력 기업인 삼성전자, 현대차로 포지셔닝했다"며 "미국 밸류체인에 로봇을 공급할 수 있는 곳은 보스턴다이내믹스 등 3곳에 불과해 추가 기업가치 평가가 기대된다는 점에 착안했다"고 말했다. 미국 조지아주 엘라벨에 있는 현대차그룹 메타플랜트 아메리카(HMGMA) 차체 공장에서 보스턴 다이내믹스의 4족 보행 로봇 \'스팟\'이 차체의 품질 검사를 하는 모습. / 사진=현대차그룹하나자산운용도 다음달 9일 \'1Q 현대차기아채권혼합50\' ETF를 출시할 계획이다. 현대차와 기아를 각각 25%씩 담고, 나머지 50%는 채권으로 구성하는 구조다. 총보수는 0.10%다. 하나자산운용은 현대모비스 등 다른 그룹 계열사 편입도 검토했지만 거래량과 시가총액 등 시장 대표성을 고려해 현대차와 기아 두 종목에 집중하는 전략을 택한 것으로 알려졌다.채권혼합형 ETF는 퇴직연금(DC·IRP) 계좌에서 활용도가 높다는 점에서 최근 빠르게 시장이 커지고 있다. 현행 제도상 퇴직연금 계좌는 위험자산 투자 비중이 70%로 제한되지만 주식 비중이 50% 미만인 채권혼합형 ETF는 안전자산으로 분류돼 연금 계좌에서 100% 편입할 수 있다.실제 KB자산운용이 지난 2월 선보인 \'RISE 삼성전자SK하이닉스채권혼합50\'은 삼성전자와 SK하이닉스를 각각 25%씩 담고 총보수를 연 0.01%까지 낮추며 흥행에 성공했다. 해당 ETF는 출시 3개월 만에 순자산(AUM) 2조 7000억 원을 돌파하며 올해 신규 상장 ETF 가운데 가장 많은 자금을 끌어모았다. 지난 4월에는 삼성자산운용이 비슷한 구조의 \'KODEX 삼성전자SK하이닉스채권혼합50\'을 상장했고 한 달 반 만에 9000억원이 넘는 자금이 유입됐다.최근 시장에서는 현대차를 자동차 업종을 넘어 AI·로봇 등을 아우르는 \'피지컬AI 플랫폼\' 기업으로 재평가하는 모습이다. 현대차 주가가 최근 한 달간 29.2% 상승한 가운데, 현대모비스(58.61%), 현대오토에버(69.16%) 등 주요 계열사도 나란히 불기둥을 세웠다. 현대차의 로봇 계열사인 보스턴다이나믹스의 휴머노이드 로봇 \'아틀라스\'에 대한 기대가 커지면서 현대차 주가는 올해만 129.7% 올랐다.증권가에서는 현대차그룹 목표주가를 줄줄이 높여 잡고 있다. 이달 들어 증권사 10곳에서 현대차의 목표가를 상향 조정했다. 목표가 최고치는 KB증권이 제시한 120만원이다. 강성진 KB증권 연구원은 "보스턴다이내믹스의 2035년 시장 점유율을 44.3%로 전망한다"며 "현대차가 휴머노이드 산업 선도함으로써 전세계 피지컬 AI 산업의 대표 주자로 도약할 것"이라고 내다봤다.'}, {'article': '미국 AI 투자 기대감 확대…반도체주 전반 매수세 유입 [수원=뉴시스] 김종택기자 =경기 수원시 영통구 삼성전자 수원본사 모습. 2026.05.27. jtk@newsis.com[서울=뉴시스]송혜리 기자 = 삼성전자가 29일 장 초반 5% 넘게 급등하면서 관련 레버리지 상장지수펀드(ETF)도 일제히 치솟고 있다. 미국발 인공지능(AI) 투자 기대감이 다시 살아나며 반도체주 전반에 매수세가 몰리는 분위기다.한국거래소에 따르면 삼성전자는 이날 3%대 강세로 출발한 뒤 상승폭을 확대했다. 오전 9시20분 기준 삼성전자는 전 거래일보다 3.48% 오른 31만1000원에 거래되고 있다. 장중에는 5% 이상 급등하기도 했다.삼성전자 강세에 단일 종목 레버리지 상장지수펀드(ETF)도 급등세를 나타냈다. 코덱스 삼성전자레버리지는 8.29%, 라이즈 삼성전자레버리지는 8.56% 상승했다. 에이스 삼성전자레버리지는 7.89%, 타이거 삼성전자레버리지는 8.81% 오르며 나란히 강세를 나타냈다.간밤 뉴욕증시에서는 AI 관련 기대감이 다시 살아나며 기술주가 상승세를 주도했다. CNBC 등에 따르면 클라우드 기반 데이터 플랫폼 업체 스노우플레이크는 호실적과 긍정적인 실적 전망을 발표한 뒤 주가가 약 37% 급등했다.스노우플레이크는 지난 분기 매출과 순이익이 시장 예상치를 웃돌았고, 2분기 실적 가이던스 역시 기대를 상회했다. 여기에 향후 5년간 아마존웹서비스(AWS)에 60억달러를 투자하겠다는 계획까지 공개하면서 AI 인프라 투자 확대 기대감을 키웠다.메모리 반도체 관련 종목들도 강세를 나타냈다. 샌디스크는 3% 상승했고 퀄컴과 AMD는 각각 4% 넘게 올랐다. 엔비디아 역시 0.78% 상승 마감하며 AI 반도체 랠리를 이어갔다．'}
            ] """
            return [FinanceArticle.model_validate(item) for item in articles]

        except Exception as e:
            print(exception_format(e))
            raise

        finally:
            await self.pm.close()