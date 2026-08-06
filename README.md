# 티스토리 자동 포스팅 API

FastAPI 기반 뉴스 큐레이션 자동 포스팅 서비스.

네이버 금융·연예 랭킹 뉴스를 Playwright 로 스크래핑하고, LLM(`llama-3.1-8b-instant`)으로
마크다운 블로그 포스트(제목·본문·태그)로 가공한 뒤 티스토리에 자동 발행합니다.

![Architecture](storage/screenshots/architecture.png)

---

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| API | FastAPI, Uvicorn, Pydantic v2 |
| 브라우저 자동화 | Playwright 1.58.0 (chromium) |
| LLM | Groq `llama-3.1-8b-instant` (`response_format=json_object`) |
| RDB | MySQL 8.0 (SQLAlchemy 2.0.47, aiomysql, Alembic) |
| 큐 / 캐시 | Redis 7.4.0 |
| Auth | python-jose (JWT) |
| 패키지 관리 | uv |

---

## 핵심 특징

| 영역 | 내용 |
|---|---|
| **뉴스 스크래핑** | Playwright 로 네이버 랭킹 뉴스에서 랜덤 2건 선정 → 새 탭에서 본문 추출 후 닫기 |
| **LLM 요약** | 기사 본문 → JSON(`title`, `content`, `tags`) 변환. `response_format={"type": "json_object"}` 로 파싱 안정성 확보 |
| **콘텐츠 규격 강제** | 시스템 프롬프트로 25~32자 제목 + 800~1200자 마크다운 본문 + `\|\|` 구분 태그 5개 |
| **로그인 세션 재사용** | 카카오 OAuth 첫 로그인 후 `storage_state` 를 파일로 저장 → 이후 실행은 자동 로그인 |

---

## 디렉토리 구조

```text
fastapi-tistory/
├── app/
│   ├── api/
│   │   ├── __init__.py                     # /api 루트 + collect_routers 자동 수집
│   │   └── v1/
│   │       ├── __init__.py                 # /v1 + 하위 라우터 자동 등록
│   │       └── tistory/
│   │           ├── __init__.py             # /tistory + 하위(finance/entertain) 자동 수집
│   │           ├── router.py               # tistory 직속 라우트
│   │           ├── finance/router.py       # 금융 scrap / summarize / publish / run
│   │           └── entertain/router.py     # 연예 scrap / summarize / publish / run
│   ├── core/
│   │   ├── config.py                       # pydantic-settings, BASE_DIR, STORAGE_PATH, TISTORY_STORAGE
│   │   ├── logger.py                       # 전역 logger + setup_logging
│   │   ├── dependencies/tistory.py         # 스크래퍼·요약·포스트 서비스 DI
│   │   ├── exceptions/
│   │   │   ├── custom.py                   # 비즈니스 예외
│   │   │   └── handlers.py                 # 글로벌 예외 핸들러 등록
│   │   └── utils/
│   │       ├── error.py                    # exception_format
│   │       ├── file.py                     # ensure_directory
│   │       ├── log.py                      # save_log (일자별 파일 로그)
│   │       ├── notebook.py                 # run_async (백그라운드 Proactor 루프)
│   │       ├── response.py                 # 성공/오류 응답 헬퍼
│   │       └── router.py                   # collect_routers (라우터 자동 수집)
│   ├── modules/
│   │   ├── browser/playwright.py           # PlaywrightManager (start/close/create_context)
│   │   └── llm/
│   │       ├── groq.py                     # create_async_groq_client
│   │       └── config.py                   # LLMConfig (모델별 파라미터)
│   ├── prompts/
│   │   ├── finance_news.py                 # FINANCE_NEWS_SYSTEM_PROMPT
│   │   └── entertain_news.py               # ENTERTAIN_NEWS_SYSTEM_PROMPT
│   ├── schemas/
│   │   ├── base.py                         # BaseResponse 제네릭
│   │   ├── enums.py                        # BlogCategory, 예약 방식 Enum
│   │   └── tistory/
│   │       ├── article.py                  # NewsArticle, SummarizedArticle, ReservationData
│   │       ├── request.py                  # TistorySummarizeRequest, TistoryPublishRequest
│   │       └── response.py                 # PostingResponse
│   ├── services/
│   │   ├── scraper/
│   │   │   ├── base.py                     # ScraperBase (스크래퍼 공통 베이스)
│   │   │   ├── finance_news.py             # FinanceNewsScrapService
│   │   │   └── entertain_news.py           # EntNewsScrapService
│   │   ├── llm/news_summarize.py           # NewsSummarizeService (summarize_one/many)
│   │   └── tistory/
│   │       ├── login.py                    # TistoryLoginService (카카오 OAuth → storage_state 저장)
│   │       └── post.py                     # TistoryPostService (글쓰기/발행 전체)
│   └── main.py                             # FastAPI 진입점
├── notebooks/tistory/
│   ├── login.ipynb                         # 최초 카카오 로그인 → 세션 저장
│   └── news_post.ipynb                     # 전체 자동화 파이프라인
├── storage/
│   ├── tistory/browser_context.json        # 카카오/티스토리 로그인 세션
│   └── logs/                               # save_log 가 쓰는 카테고리별 일자 로그
├── tests/
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 실행

```bash
docker compose up -d
```

| 서비스 | 주소 |
|---|---|
| API (Swagger) | http://localhost:9095/docs |
| MySQL | localhost:3306 |
| Redis | localhost:6379 |

**사전 조건** — 카카오 최초 로그인은 2FA·캡차 때문에 수동입니다.
`notebooks/tistory/login.ipynb` 를 한 번 실행해 `storage/tistory/browser_context.json` 세션을 만들어두면
이후 발행은 자동으로 동작합니다.

---

## API

모든 엔드포인트는 `/api/v1/tistory/{finance|entertain}` 아래에 있으며, 두 도메인의 스키마는 같고 프롬프트만 다릅니다.

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/scrap` | 랭킹 뉴스 랜덤 2건 스크래핑 |
| `POST` | `/summarize` | 기사 본문 → LLM 요약 (`title` / `content` / `tags`) |
| `POST` | `/publish` | 요약 결과를 티스토리에 발행 (`reservation_data` 로 예약 발행) |
| `POST` | `/run` | scrap → summarize → publish 전체 (예정) |

응답은 `{ "code": "200", "data": {...} }` 봉투로 감쌉니다. (`code` 는 문자열)

| 상황 | 코드 |
|---|---|
| 요청 검증 실패 (필드 누락 / 과거 예약일 등) | `422` |
| 비즈니스 규칙 위반 (`BusinessException`) | `400` |
| 티스토리 세션 만료 | `401` |
| Playwright timeout, LLM JSON 위반 | `500` |

---

## 처리 흐름

1. **스크래핑** — 네이버 랭킹 뉴스 리스트에서 `random.sample(k=2)` → 각 항목 클릭 → 새 탭 본문 추출 → 탭 닫기
2. **요약** — `asyncio.gather` 로 기사 병렬 요약. 제목 후처리(줄바꿈 제거, 32자 초과 시 절단)
3. **발행** — `storage_state` 로 로그인 우회 → 글쓰기 페이지 진입
   - 다이얼로그 분기: `"이어서 작성"` → dismiss / 모드 변경 confirm → accept
   - 마크다운 모드 전환 후 CodeMirror 에 `setValue()` → `save()` → `input/change` 이벤트 디스패치
   - 태그 입력 후 "완료" → "공개 발행" 클릭

> 프롬프트 규칙(`app/prompts/`): 제목 32자 초과 금지, 본문 큰따옴표 금지(JSON escape 보호),
> 일본어·중국어 금지, SEO 키워드 3~5회 반복, 태그 `\|\|` 구분 5개 이내.

---

## 노트북 사용

Windows 의 Jupyter 기본 `SelectorEventLoop` 는 subprocess 를 지원하지 않아 Playwright 가 동작하지 않습니다.
별도 백그라운드 스레드에서 `ProactorEventLoop` 를 띄우는 `run_async` 헬퍼를 사용하세요.

```python
from app.core.utils.notebook import run_async

articles = run_async(fns.do_scraping())
summarized = run_async(ns.summarize_many(articles))
run_async(poster.do_posting(summarized))
```

`run_async` 로 호출된 코루틴은 모두 **같은 백그라운드 루프**에서 실행되어 Browser/Context/Page 를 셀 간에 유지할 수 있습니다.

---

## 로깅

| | `logger` (콘솔/stderr) | `save_log` (파일) |
|---|---|---|
| 위치 | `app/core/logger.py` | `app/core/utils/log.py` |
| 목적 | 디버깅·실시간 모니터링 | 영구 기록·통계 |
| 포맷 | 시각 + 레벨 + 파일경로:라인 + 메시지 | 시각 + 메시지 |
| 출력 | stderr | `storage/logs/<카테고리>/YYYY-MM-DD.log` |

---

## 개선해야할 점

| 항목 | 내용 |
|---|---|
| 카카오 최초 로그인 | 2FA·캡차로 첫 로그인은 수동. 세션 만료 시 감지·알림 필요 |
| LLM 재시도 | `RateLimitError` / `JSONDecodeError` 캐치 후 백오프 재시도 부재 |
| 이미지 첨부 | 본문이 텍스트 마크다운만. placeholder → 이미지 검색·업로드 치환 필요 |
| 결과 영속화 | MySQL 이 docker-compose 에만 있고 미연결. 발행 이력 저장으로 중복 발행 방지 필요 |
| 워커 분리 | `worker` 컨테이너는 있으나 Redis 큐 통합 미완 → `/run` 즉시 응답 + 백그라운드 처리 전환 |
| 응답 스키마 | 라우터 `response_model` 과 실제 반환 타입 정합 미흡 |
| 테스트 | `tests/` 에 샘플만 존재 |

---

## 실행 화면

![티스토리 자동 포스팅](storage/screenshots/news_post.gif)
