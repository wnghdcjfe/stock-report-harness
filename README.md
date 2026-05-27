# stock-report-harness

주식·ETF·섹터 요청을 **계획 → 리서치 → 원고 → 이미지 → 리뷰 → 빌드** 파일 계약으로 처리해 검증 가능한 HTML 경제리포트를 만드는 Claude Code용 하네스입니다.

> 현재 코드 기준: 리포트 산출물은 `plan/`, `research/`, `drafts/`, `reviews/`, `output/` 아래 파일로 연결되며, 최종 HTML은 `review status: pass`와 선택된 hero 이미지가 있어야만 빌드됩니다.

## 전체 파이프라인

```text
User Request
  ↓
Planner             -> plan/<slug>.md
  ↓
Research Generator  -> research/<slug>.md + output/assets/*latest100.json 등 원자료
  ↓
Report Generator    -> drafts/<slug>.md
  ↓
Image Generator     -> output/assets/<slug>-hero-v1~v3.* + selected-image.json
  ↓
4-way Evaluators    -> reviews/<slug>.md
  ↓
Builder             -> output/<slug>.html + output/assets/<slug>-price-chart-v*.json
```

핵심 원칙은 `plan/<slug>.md`가 후속 단계의 단일 기준 문서가 된다는 점입니다. 리서치, 원고, 이미지, 리뷰, 빌드는 모두 같은 slug의 선행 산출물을 참조합니다.

## 디렉터리와 주요 파일

```text
.claude/
  agents/
    fact-checker.md
    report-designer.md
    content-editor.md
  skills/
    plan/ research/ draft/ image/ review/ build/ ask-gpt/
  hooks/
    block-dangerous-bash.sh
    enforce-plan.sh
    enforce-citations.sh
    remind-review.sh
    review-feedback-loop.sh
    forbid-financial-advice.sh
    protect-sensitive-files.sh
    inject-memory-context.sh
    enforce-memory.sh

docs/
  finance-style-guide.md
  output-spec.md
  pedagogy.md
  visual-system.md
  image-generation-spec.md
  templates/planning-brief-template.md
  templates/report-template.md

scripts/
  memory_context.py
  news_latest5.py
  validate_memory.py

plan/ research/ drafts/ reviews/ output/
server.js
```

## Claude skill 명령

| 명령 | 입력 | 주요 출력 |
|---|---|---|
| `/plan <요청>` | 자연어 요청 | `plan/<slug>.md` |
| `/research <slug>` | 같은 slug의 plan | `research/<slug>.md`, 필요 시 `output/assets/*latest100.json` |
| `/draft <slug>` | plan + research | `drafts/<slug>.md` |
| `/image <slug>` | plan + research + draft | hero 후보 3개, manifest, score, selected-image |
| `/review <slug>` | plan + research + draft | `reviews/<slug>.md` |
| `/build <slug>` | 통과 리뷰 + draft + selected image | `output/<slug>.html`, yfinance chart JSON |
| `/ask-gpt <질문>` | 자유 질문 | Codex CLI 교차 의견 |

일반 순서:

```text
/plan → /research → /draft → /image → /review → /build
```

## Plan 계약

`plan/<slug>.md` frontmatter는 다음 필드를 기준으로 합니다.

```yaml
---
slug: <slug>
topic: <리포트 주제>
request: <원문 요청>
output_type: report
audience: beginner | intermediate | advanced
ticker: <yfinance symbol 또는 TBD>
period_start: YYYY-MM-DD
period_end: YYYY-MM-DD
chart_required: true | false
price_data_source: yfinance
price_data_interval: 1d
created_at: YYYY-MM-DD
assumptions:
  - <Planner 가정>
---
```

Planner는 기간, ticker, 차트 필요 여부, 리서치 범위, 리포트 구조, hero 이미지 방향, 리뷰 기준, 차단 조건을 고정합니다. 사용자가 기간을 말하지 않으면 기본값은 최근 6개월입니다.

## Research 계약

`/research`는 plan을 읽고 `research/<slug>.md`를 작성합니다.

필수 확인 항목:

- `ticker`, `period_start`, `period_end`
- yfinance 기준 가격 데이터 요구사항: `interval=1d`
- 주요 뉴스, 공시, 실적, 리스크
- 종목 관련 요청이면 종목별 최신 뉴스 최소 100건
- 한국 상장 종목이면 가능할 때 토스증권 뉴스·투자자별 매매 동향
- 항목별 URL 또는 fallback URL 여부

뉴스 원자료는 가능하면 `output/assets/<slug>-*-latest100.json`, 분석 결과는 `output/assets/<slug>-*-analysis100.json`처럼 남깁니다. URL이 제공되지 않는 API는 원문 URL을 추측하지 않고 `url_is_fallback` 또는 본문 주석으로 표시합니다.

## Draft 계약

`drafts/<slug>.md`는 plan과 research를 모두 참조해야 합니다.

필수 frontmatter 예시:

```yaml
---
slug: nvidia-recent-6m-2026-05
title: 엔비디아 최근 6개월 경제리포트
subtitle: 주가 흐름과 핵심 촉매를 함께 보는 리포트
ticker: NVDA
period_start: 2025-11-26
period_end: 2026-05-26
level: beginner
duration_minutes: 12
created_at: 2026-05-26
plan_source: plan/nvidia-recent-6m-2026-05.md
research_source: research/nvidia-recent-6m-2026-05.md
---
```

가격 차트는 숫자 배열을 원고에 직접 넣지 않고 `price-chart` 블록으로 선언합니다.

````markdown
```price-chart
title: 엔비디아 최근 6개월 일별 종가
aria_label: 엔비디아의 요청 기간 전체 일별 종가 추이 차트
field: Close
interval: 1d
currency: USD
```
````

원고에는 다음이 필요합니다.

- 정확히 1개의 H1
- `## 개요`, `## 배경`, `## 메커니즘`, `## 영향과 적용` 필수 섹션
- `## References`
- 투자 유의/면책 문구
- 관련 뉴스 100건이 있으면 `## 최신 뉴스 5건 요약`
- 본문 숫자·가격 해석의 검증용 출처 표식

최종 HTML에서는 `[S1]`, `[N1]` 같은 검증용 인라인 표식이 제거되고 References 섹션만 남습니다.

## Image 계약

`/image`는 전체 리포트 기반 hero 이미지 후보 3개를 만들고 선택 기록을 남기는 단계입니다.

필수 산출물:

```text
output/assets/<slug>-hero-v1.prompt.txt
output/assets/<slug>-hero-v2.prompt.txt
output/assets/<slug>-hero-v3.prompt.txt
output/assets/<slug>-hero-v1.png
output/assets/<slug>-hero-v2.png
output/assets/<slug>-hero-v3.png
output/assets/<slug>-hero-v1.score.json
output/assets/<slug>-hero-v2.score.json
output/assets/<slug>-hero-v3.score.json
output/assets/<slug>-image-manifest.json
output/assets/<slug>-image-review.txt
output/assets/<slug>-selected-image.json
```

프롬프트 생성 스크립트:

```bash
python3 .claude/skills/build/scripts/make-image-prompt-variants.py \
  --draft drafts/<slug>.md \
  --assets-dir output/assets
```

선택 스크립트:

```bash
python3 .claude/skills/build/scripts/select-best-image.py \
  --manifest output/assets/<slug>-image-manifest.json \
  --selected-out output/assets/<slug>-selected-image.json
```

이미지는 텍스트, 숫자, 티커, 로고, 워터마크, UI 스크린샷을 넣지 않는 프리미엄 editorial hero 스타일을 기준으로 합니다.

## Review 계약

`/review`는 메인 세션 직접 판단이 아니라 별도 세션 기반 4-way review입니다.

| 리뷰어 | 실행 방식 | 책임 |
|---|---|---|
| `fact-checker` | Task subagent | ticker, 기간, 숫자, 가격, 출처, research/draft 정합성 |
| `report-designer` | Task subagent | 리포트 구조, 독자 흐름, 차트/hero 연결성 |
| `content-editor` | Task subagent | 문장 품질, 톤, 중복, 투자 권유 표현 제거 |
| Codex independent review | `gpt-review.sh` / `gpt-review.ps1` | blind spot, 논리 비약, plan 누락 교차 검토 |

리뷰 frontmatter 필수값:

```yaml
---
slug: <slug>
status: pass | needs_fix | blocked
reviewed_at: YYYY-MM-DDTHH:mm:ssZ
plan_source: plan/<slug>.md
research_source: research/<slug>.md
draft_source: drafts/<slug>.md
review_type: separate-session-4way
review_execution: separate_subagent_sessions
reviewers: fact-checker, report-designer, content-editor, codex-independent
---
```

`status: needs_fix`이면 파이프라인은 멈추지 않고 `/research`, `/draft`, `/image`, 필요 시 `/plan`으로 돌아가 수정한 뒤 같은 slug로 `/review`를 다시 실행해야 합니다. 같은 차단 이슈가 3회 반복되거나 외부 데이터/권한 때문에 해결할 수 없을 때만 `blocked`로 남깁니다.

## Build 계약

실행:

```bash
bash .claude/skills/build/scripts/build-html.sh --slug <slug>
```

또는 내부 Python 진입점:

```bash
python3 .claude/skills/build/scripts/build-html.py \
  --draft drafts/<slug>.md \
  --output output/<slug>.html
```

Build가 검증하는 조건:

- `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`, `reviews/<slug>.md` 존재
- review `status: pass`
- review `review_type: separate-session-4way`
- review `review_execution: separate_subagent_sessions`
- draft `plan_source`, `research_source`, `ticker`, `period_start`, `period_end`, `level`, `duration_minutes`
- plan/research/draft의 ticker·기간 일치
- 정확히 1개의 H1
- 필수 섹션: 개요, 배경, 메커니즘, 영향과 적용
- References 섹션 존재
- 본문 footnote 번호 금지
- yfinance 기반 price chart 최소 1개
- 가격 차트 기간은 366일 이내
- 차트 label은 `YYYY-MM-DD` 오름차순
- 모든 차트에 `ariaLabel`
- `output/assets/<slug>-selected-image.json` 및 실제 이미지 파일 존재

Build 결과:

- `output/<slug>.html`
- `output/assets/<slug>-price-chart-v1.json` 등 yfinance 원자료
- HTML 메타 generator: `stock-report-harness v1`
- Chart.js v4 CDN 사용
- Pretendard 폰트 CDN 사용
- 다크모드, 목차, hero 이미지, chart summary card 포함

## 최신 뉴스 5건 도우미

`output/assets/*latest100.json`에서 최신 5건을 결정론적으로 뽑는 도구입니다.

```bash
python3 scripts/news_latest5.py output/assets/<slug>-*-latest100.json --format markdown
python3 scripts/news_latest5.py output/assets/<slug>-*-latest100.json --format html
python3 scripts/news_latest5.py output/assets/<slug>-*-latest100.json --format json
```

지원하는 날짜 키: `published_at_utc`, `publishedAt`, `createdAt`, `updatedAt`, `date`.
지원하는 URL 키: `url`, `link`, `article_url`, `articleUrl`, `original_url`, `canonical_url`, `google_news_link`, `news_url` 등.

URL이 없으면 `--fallback-stock-news-url`을 쓰거나 제목 기반 Google 검색 URL을 fallback으로 생성하고 fallback임을 표시합니다.

## Hook 가드레일

`.claude/settings.json`에 등록된 hooks가 다음을 강제합니다.

| Hook | 시점 | 역할 |
|---|---|---|
| `block-dangerous-bash.sh` | PreToolUse Bash | 위험 shell 명령 차단 |
| `protect-sensitive-files.sh` | PreToolUse Edit/Write | `.env`, `.git`, workflow, 핵심 docs 보호 |
| `forbid-financial-advice.sh` | PreToolUse Edit/Write | drafts/output 투자 권유·사기성 표현 차단 |
| `enforce-plan.sh` | Stop | plan → research → draft → image/review/build 순서 강제 |
| `review-feedback-loop.sh` | Stop | `needs_fix` 리뷰 후 generator 재실행 강제 |
| `enforce-citations.sh` | Stop | 변경 draft의 면책·숫자 출처 1차 점검 |
| `remind-review.sh` | Stop | draft 변경 후 4-way review 증거 요구 |
| `enforce-memory.sh` | Stop | memory 변경 시 schema 검증 |
| `inject-memory-context.sh` | UserPromptSubmit | prompt 도메인별 memory topic 자동 주입 |

## Memory system

반복 실패를 줄이기 위한 관측 기반 메모리입니다.

```text
memory/
  _template.md
  _daily/YYYY-MM-DD.md
  topics/{slug}.md
```

검증:

```bash
python3 scripts/validate_memory.py
```

프롬프트 도메인 선택기 수동 테스트:

```bash
echo '{"prompt":"/build samsung-electronics-recent-30d-2026-05 이미지 빌드"}' | python3 scripts/memory_context.py
```

## 로컬 미리보기 서버

`server.js`는 `output/` 디렉터리를 정적 파일로 제공합니다.

```bash
node server.js
# Serving .../output at http://localhost:3000
```

환경변수 `PORT`로 포트를 바꿀 수 있습니다.

## 의존 도구

- Python 3
- `yfinance` 및 Python 데이터 의존성
- `jq` (hook 스크립트)
- Node.js (선택: `server.js` 미리보기)
- `claude` CLI (선택: Playwright MCP research 스크립트)
- `codex` CLI (선택: `/ask-gpt`, Codex independent review)
- 이미지 생성은 Claude/Codex의 `imagegen` skill 또는 `image_gen` 도구 사용

## 금지/주의 사항

- plan 없이 research/draft/build 산출물을 만들지 않습니다.
- research 없이 draft를 만들지 않습니다.
- review 없이 build하지 않습니다.
- selected hero 이미지 없이 build하지 않습니다.
- 임의 가격 데이터나 샘플링 차트를 넣지 않습니다.
- 항목별 기사 URL을 제공하지 않는 API에서 원문 URL을 조작해 만들지 않습니다.
- 투자 자문, 수익 보장, 매매 지시처럼 읽히는 표현을 쓰지 않습니다.

## 현재 예시 산출물

저장소에는 다음 예시 산출물이 포함되어 있습니다.

- `nvidia-recent-4m-2026-05`
- `nvidia-recent-6m-2026-05`
- `samsung-electronics-recent-1y-2026-05`
- `samsung-electronics-recent-30d-2026-05`
- `tesla-recent-6m-2026-05` 일부 원자료

예시 HTML은 `output/*.html`에서 확인할 수 있습니다.
