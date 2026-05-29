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
            model=LLMConfig.MODELS['llama']['3.1-8b-instant']['model'],
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


    async def summarize_many(self, articles: list[dict[str, str]]):
        tasks = [self.summarize_one(article['article']) for article in articles]
        return await asyncio.gather(*tasks)