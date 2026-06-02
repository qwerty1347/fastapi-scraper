import asyncio
import json

from groq import AsyncGroq

from app.modules.llm.prompt import FINANCE_NEWS_SYSTEM_PROMPT
from config.llm import LLMConfig


class NewsSummarizeService:
    def __init__(self, client: AsyncGroq):
        self.client = client


    async def summarize_one(self, article: str):
        response = await self.client.chat.completions.create(
            model=LLMConfig.MODELS['llama']['3.3-70b-versatile']['model'],
            messages=[
                {"role": "system", "content": FINANCE_NEWS_SYSTEM_PROMPT},
                {"role": "user", "content": article}
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

        # 제목 정리: 줄바꿈/따옴표/공백 제거, 첫 줄만 사용
        title = result.get("title", "").strip().strip('"\'')
        title = title.split("\n")[0].strip()
        result["title"] = title

        return result


    async def summarize_many(self, articles: list[dict[str, str]]) -> list[dict[str, str]]:
        tasks = [self.summarize_one(article['article']) for article in articles]
        summarized = await asyncio.gather(*tasks)
        # ! 하드코딩
        """ summarized = [
            {'title': '현대차 ETF 출시에 앞서...현대차 목표주가 한자리수 인상해', 'content': "# 현대차 ETF 출시에 앞서...현대차 목표주가 한자리수 인상해\n\n로봇 사업이 주효했던 현대차. 금융투자업계 'KODEX 현대차로보틱스밸류체인TOP3플러스' 출시에 앞서 현대차그룹의 로봇 계열사인 현대모비스의 주주는 주당 3만8000원에서 주당 6만원으로 58.6% 상승했다. 증권가는 현대차가 피지컬 AI 산업의 핵심 플레이어로 부상한다며 목표주가를 줄줄이 상향 조정했다.\n\n## 현대차 주가 29.2% 상승\n\n지난 한 달만에 현대차 주가는 29.2%가 넘는 폭을 기록했다. 24만4000원에서 31만6000원으로 오른 현대차 주가는 올해만 129.7%를 기록했으며, 주요 계열사인 현대모비스와 현대오토에버도 나란히 오르는 모습을 보여주고 있다.\n\n## 현대차 목표주가 120만원까지 상향 조정\n\n증권가에서는 현대차그룹의 목표주가를 상향 조정하고 있다. 이달 들어 증권사 10곳에서 현대차의 목표가를 상향 조정하고 있으며, 최고로는 KB증권의 120만원이다.\n\n**보스턴다이내믹스 2035년 시장 점유율 44.3% 전망**\n\n KB증권은 보스턴다이내믹스의 2035년 시장 점유율을 44.3%로 전망하고 있다. 현대차가 로봇 사업 통해 전세계 피지컬 AI 산업의 대표주자로 도약할 것이라고 전망했다.\n\n현대차는 로봇 사업과 관련된 다양한 노력을 하고 있다. 보스턴다이내믹스와의 협력이 이러한 노력의 한 부분으로 보기는 힘들다. 현대차의 로봇 사업이 주효했던 것은 분명하다. 금융투자업계의 ETF 출시에 앞서 현대차의 기대가 크다. 현대차 주가와 목표주가가 오를 수 밖에 없다.", 'tags': '현대차||로봇||ETF||투자||보스턴다이내믹스||피지컬AI||AI'}, {'title': '미국 AI 투자 기대감 확대…반도체주 전반 매수세 유입', 'content': '### 미국 AI 투자 기대감 확대\n\n인공지능(AI) 투자 기대감이 다시 살아난다.\n\n#### 삼성전자가 반전\n\n삼성전자가 29일 장 초반 5% 넘게 급등한 것은 관련 레버리지 상장지수 펀드도 일제히 치솟고 있는 반도체 주 전반 매수세 유입으로 보인다. 한국거래소에 따르면 삼성전자는 이날 3%대 강세로 출발한 뒤 상승폭을 확대했다.\n\n#### AI 투자 확대\n\n이와 관련해 미국에서 AI 관련 기대감이 다시 살아났다는 보도가 나왔다. 뉴욕증시에서는 기술주가 상승세를 주도했고, 클라우드 기반 데이터 플랫폼 업체 스노우플레이크의 호실적과 긍정적인 실적 전망 발표로 주가가 약 37% 급등했다.\n\n#### 반도체주 강세도 예상\n\n또한 스노우플레이크의 향후 5년간 아마존 웹 서비스(AWS)에 60억달러를 투자하겠다는 계획 발표로 AI 인프라 투자 확대 기대감을 키웠다. 메모리 반도체 관련 종목들도 강세를 나타냈다. 샌디스크는 3% 상승했고 퀄컴과 AMD는 각각 4% 넘게 올랐다. 엔비디아 역시 0.78% 상승 마감하며 AI 반도체 랠리를 이어갔다.\n\n### 핵심 키워드\n\n반도체주 · AI 투자 · 인공지능', 'tags': '반도체주||AI투자||인공지능||삼성전자||스노우플레이크||메모리반도체'}
        ] """
        return summarized