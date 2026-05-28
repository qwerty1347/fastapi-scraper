# fastapi-scraper 작업 절차 (개요)

스크래핑 → LLM 글 생성 → Tistory 자동 발행 파이프라인의 단계별 개요입니다.
(각 단계 상세 문서는 별도 작성 예정)

## 전체 파이프라인

```
[1] 스크래핑  →  [2] LLM 글 생성  →  [3] Tistory 발행
```

### 1. 스크래핑 (예정)
- 대상 소스에서 원문/소재 데이터 수집
- 정제 후 LLM 입력용 텍스트로 가공

### 2. LLM 글 생성 (예정)
- 수집 데이터를 프롬프트로 변환
- LLM 호출 → 제목 + 본문(HTML) 생성
- 결과 검증/후처리

### 3. Tistory 발행 (구현됨, Playwright 자동화)

#### 3-1. 로그인 & 세션 저장 (최초 1회)
- `scripts/tistory/login.py` — 카카오 계정 로그인
- 로그인 완료 후 브라우저 컨텍스트를 `storage/tistory/browser_context.json` 으로 저장
- 실행: `uv run python -m scripts.tistory.main login`

#### 3-2. 글 발행
- 저장된 컨텍스트(세션) 로드 → 로그인 상태 복원
- 메인 페이지 진입 → `글쓰기` 클릭 → 에디터 페이지 오픈
- 제목(`#post-title-inp`) / 본문(`#editor-tistory_ifr` 내 `#tinymce`) 입력
- `완료` → 공개 설정 → `공개 발행`
- 실행 경로:
  - 스크립트: `uv run python -m scripts.tistory.main post`
  - API: `GET /tistory/post`

## 사전 준비
- 의존성 설치 후 Playwright 브라우저 엔진 설치
  - `uv run playwright install chromium`
- `.env` 에 `STORAGE_PATH` 설정 (`.env.example` 참고)

## 현재 상태
- [x] Tistory 로그인 / 세션 저장
- [x] Tistory 글 발행 자동화 (제목·본문 하드코딩 상태)
- [ ] 스크래핑 모듈
- [ ] LLM 글 생성 모듈 + 발행 단계 연동(하드코딩 → 생성 결과 주입)

<br>

# 추가 검토 사항 (DB / 비동기 처리)

### DB 연동 — 도입 권장
이미 인프라 준비됨: docker-compose에 MySQL + MongoDB, 의존성에 `beanie`/`motor`/`sqlalchemy`/`alembic`.

영속화 대상:
- **스크래핑 결과** — 중복 수집 방지(dedup), 재처리용 원문 보관
- **LLM 생성 글** — 발행 전 검토/재생성, 실패 시 재시도
- **발행 이력** — 성공/실패, Tistory 글 URL, 에러 로그

→ `article` 문서에 상태 필드(`scraped → generated → published`)로 추적.
스크랩 데이터는 스키마 유동적이라 **MongoDB(beanie)** 권장.

### Celery — 현 시점 불필요 (조건부 도입)
발행은 Playwright + LLM 호출로 수십 초~분 소요 → 동기 HTTP 요청은 블로킹/타임아웃 위험.
단, Celery가 곧 필요하다는 뜻은 아님:

- **단건 발행만** → FastAPI `BackgroundTasks` 또는 CLI 스크립트로 충분
- **정기/대량 발행, 재시도·큐 필요해지면** → 도입 검토

이 프로젝트는 async 스택(async Playwright)이라 도입 시점에도 Celery보다:
- **APScheduler** — 정기 자동 발행 목적이면 인프라 추가 없이 인프로세스로 충분
- **arq** — Redis 기반 async 네이티브, 큐/재시도 필요 시 Celery 대안

권장 순서: ① DB 연동 + 발행 비동기화(BackgroundTasks) → ② 정기 발행 필요 시 APScheduler → ③ 본격 큐 필요 시 arq
