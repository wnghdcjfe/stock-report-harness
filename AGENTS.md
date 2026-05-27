# stock-report-harness 운영 지침

## 목적
이 저장소는 주식·ETF·섹터 요청을 `plan → research → draft → image → review → build` 파일 계약으로 처리해 검증 가능한 HTML 경제리포트를 만든다.
`plan/<slug>.md`는 후속 단계의 단일 기준 문서이며, 모든 산출물은 같은 `slug`의 선행 산출물을 참조한다.

## 명령과 기본 순서
- 명령: `/stock-plan <요청>`, `/stock-research <slug>`, `/stock-draft <slug>`, `/stock-image <slug>`, `/stock-review <slug>`, `/stock-build <slug>`.
- 기본 순서: `plan → research → draft → hero 이미지 3개 생성/선택 → review → build`.
- 특정 단계만 요청받아도 필요한 선행 산출물이 없으면 먼저 만든다.
- review/build에서 문제가 발견되면 같은 slug의 선행 단계로 돌아가 수정 후 재실행한다.

## Plan 계약
- `/stock-plan`은 반드시 `plan/<slug>.md`를 작성한다.
- frontmatter 필수: `slug`, `topic`, `request`, `output_type`, `audience`, `ticker`, `period_start`, `period_end`, `chart_required`, `price_data_source`, `price_data_interval`, `created_at`.
- 본문 필수: 요청 해석, 이해 목표, 리서치 범위, 데이터 확인 항목, 리포트 구조, 차트 요구, Hero 이미지 방향, 리뷰 기준, 완료/차단 조건.
- 사용자가 기간을 말하지 않으면 기본값은 최근 6개월이며 `assumptions`에 기록한다.

## Research 계약
- `/stock-research`는 `plan/<slug>.md`의 research questions와 data requirements를 따른다.
- `ticker`, `period_start`, `period_end`를 확인하고, 가격 데이터 요구는 `yfinance` 일봉(`interval=1d`)으로 둔다.
- 관련 종목(개별주/ETF/섹터 proxy)이 있으면 종목별 최신 뉴스 최소 100건을 수집·분류·분석한다.
- `research/<slug>.md`에는 100건 뉴스의 날짜, 매체, 제목, 핵심 이슈, 가격/수급/리스크 해석을 표로 남긴다.
- 뉴스 원자료 JSON에는 가능한 항목별 원문 URL을 저장한다. URL이 없으면 원문 URL을 조작하지 말고 fallback과 `url_is_fallback`을 명시한다.
- 한국 상장 종목은 가능하면 토스증권 종목 뉴스와 투자자별 매매 동향을 참고하고, 사용 URL/API를 `sources`와 원자료 JSON에 남긴다.

## Draft 계약
- `/stock-draft`는 `plan/<slug>.md`의 outline을 따르고 반드시 `research/<slug>.md`를 근거로 작성한다.
- frontmatter 필수: `ticker`, `period_start`, `period_end`, `plan_source`, `research_source`.
- 필수 섹션: H1 정확히 1개, `## 개요`, `## 배경`, `## 메커니즘`, `## 영향과 적용`, `## References`.
- 가격 차트는 직접 데이터 배열을 쓰지 말고 `price-chart` 블록으로 선언한다.
- 뉴스 100건이 있으면 `## 최신 뉴스 5건 요약`을 넣고 날짜·매체·제목 링크·1~2문장 요약·가격/수급 해석을 포함한다.
- 숫자·가격·수급·뉴스 해석에는 근거를 두고, draft/research에는 검증용 출처 표식을 유지한다.
- 투자 권유, 수익 보장, 매매 지시처럼 읽히는 표현은 금지한다.

## Image 계약
- `/stock-image`는 plan, research, draft 전체 메시지와 결론 톤을 반영해 hero 후보 3개를 만든다.
- 가능하면 `imagegen` skill 또는 `image_gen` 도구로 이미지를 직접 생성한다.
- 이미지에는 텍스트, 숫자, 티커, 로고, 워터마크, UI 스크린샷을 넣지 않는다.
- 필수 산출물: `output/assets/<slug>-hero-v1~v3.prompt.txt`, `hero-v1~v3.png`, `hero-v1~v3.score.json`, `image-manifest.json`, `selected-image.json`.
- 최종 HTML에는 선택된 hero 이미지 1장이 반드시 있어야 하며, 없으면 build를 성공 처리하지 않는다.

## Review 계약
- `/stock-review`는 별도 세션/관점의 4-way review로 수행한다.
- 리뷰어: `fact-checker`, `report-designer`, `content-editor`, `gpt-review.sh` 또는 `gpt-review.ps1`.
- `reviews/<slug>.md` frontmatter에는 `status: pass | needs_fix | blocked`, `plan_source`, `research_source`, `draft_source`, `review_type: separate-session-4way`, `review_execution: separate_subagent_sessions`를 둔다.
- 리뷰 작성 후 `python3 scripts/validate_report_contract.py <slug>`를 반드시 실행하고, 실패하면 `needs_fix`로 되돌린다.
- `needs_fix`이면 generator 단계로 돌아가 수정 후 다시 review한다. 같은 차단 이슈가 3회 반복되거나 외부 데이터/권한 때문에 해결 불가할 때만 `blocked`로 둔다.

## Build 계약
- `/stock-build`는 `plan`, `research`, `draft`, `reviews`, 선택된 hero 이미지가 모두 유효할 때만 `output/<slug>.html`을 만든다.
- build는 수동 작성이 아니라 `python3 scripts/build_report.py <slug>`로 수행한다.
- build는 `python3 scripts/validate_report_contract.py <slug> --require-html --require-price-chart`로 pass review, 4-way review metadata, frontmatter 정합성, ticker·기간 일치, 필수 섹션, References, selected image, yfinance price chart를 검증한다.
- 가격 차트는 요청 기간 전체의 실제 yfinance 일봉으로 만들고, 366일 이내·`YYYY-MM-DD` 오름차순 라벨·`ariaLabel`을 만족해야 한다.
- 최종 HTML 본문에는 `[S1]`, `[N1]` 같은 인라인 참조 표식을 노출하지 말고 References만 남긴다.
- 최종 HTML에는 투자 유의 문구를 하단 footer note로 포함하고, build 단계에서 새 주장을 추가하지 않는다.

## 금지·주의
- plan 없이 research/draft/build 산출물을 만들지 않는다.
- research 없이 draft를 만들지 않고, review 없이 build하지 않는다.
- 임의 가격 데이터, 샘플링 차트, 조작한 기사 URL을 넣지 않는다.
- `browser-use`와 직접 LLM API 키 호출은 사용하지 않는다.
- 가격 데이터는 `yfinance`를 사용하고, 웹 리서치는 검증 가능한 출처나 Playwright MCP를 우선한다.
- macOS/Linux는 `.sh`, Windows는 `.ps1` 스크립트를 우선 사용한다.

## 주요 산출물과 참조 문서
- 산출물: `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`, `reviews/<slug>.md`, `output/<slug>.html`, `output/assets/<slug>-selected-image.json`, `output/assets/<slug>-price-chart-v1.json`.
- 참조: `docs/pedagogy.md`, `docs/visual-system.md`, `docs/finance-style-guide.md`, `docs/output-spec.md`, `docs/image-generation-spec.md`, `docs/templates/*.md`.

## Memory System
- 반복 실패 방지를 위해 `docs/memory-system.md` 규칙을 따른다.
- 실패/재시도 비용이 큰 관측은 `memory/_daily/YYYY-MM-DD.md`에 append한다.
- 같은 패턴 3회 이상 또는 재발 비용이 큰 실패는 `memory/topics/{slug}.md`로 추출한다.
- memory 변경 후 `python3 scripts/validate_memory.py`를 실행한다.
- 작업 시작 시 관련 topic만 읽는다: 시간/yfinance=`time-sync`, 외부 API=`external-api`, 이미지=`image-workflow`, 단계 순서=`pipeline-order`, 빌드=`build-errors`, git=`git-workflow`, hook/validator=`guardrails`.
