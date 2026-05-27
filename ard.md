# ARD — stock-report-harness 에이전트/런타임 설명서

> 이 문서는 현재 코드 기준으로 `stock-report-harness`가 어떤 에이전트, skill, hook, 스크립트 계약으로 HTML 경제리포트를 만드는지 설명한다. 핵심은 단일 작성자가 한 번에 글을 쓰는 방식이 아니라, **파일 계약으로 분리된 계획·근거·원고·이미지·리뷰·빌드 조직**이라는 점이다.

## 1. 현재 시스템 한 줄 정의

`stock-report-harness`는 자연어 주식/시장 요청을 `plan → research → draft → image → review → build` 단계로 분해하고, 각 단계의 산출물을 파일로 남겨 최종 HTML 리포트의 근거·품질·안전성을 검증하는 Claude Code 프로젝트다.

```text
User Request
  ↓
plan/<slug>.md
  ↓
research/<slug>.md + output/assets/*latest100.json
  ↓
drafts/<slug>.md
  ↓
output/assets/<slug>-hero-v1~v3.png + selected-image.json
  ↓
reviews/<slug>.md
  ↓
output/<slug>.html + output/assets/<slug>-price-chart-v*.json
```

## 2. 설계 목표

현재 코드가 해결하려는 문제는 세 가지다.

1. **근거 체인 보존**  
   리포트 본문이 `research/`와 원자료 JSON으로 추적 가능해야 한다. 특히 종목 관련 요청은 최신 뉴스 100건, URL/fallback 여부, 가격·수급·리스크 해석을 남긴다.

2. **생성 단계와 검증 단계 분리**  
   원고를 만든 세션이 직접 통과 판정을 내리지 않는다. `fact-checker`, `report-designer`, `content-editor`, Codex independent review가 별도 관점으로 검토한다.

3. **빌드 게이트 자동화**  
   `build-html.py`는 pass 리뷰, selected image, yfinance price chart, frontmatter 정합성, 필수 섹션, References, 차트 접근성 등을 검사한 뒤 HTML을 생성한다.

## 3. Skill 기반 단계

### 3.1 `/plan`

파일: `.claude/skills/plan/SKILL.md`  
출력: `plan/<slug>.md`

Planner는 사용자의 자연어 요청을 후속 단계의 기준 문서로 바꾼다.

필수 frontmatter:

- `slug`
- `topic`
- `request`
- `output_type: report`
- `audience`
- `ticker`
- `period_start`, `period_end`
- `chart_required`
- `price_data_source: yfinance`
- `price_data_interval: 1d`
- `created_at`
- `assumptions`

본문에는 요청 해석, 이해 목표, 리서치 범위, 데이터 확인 항목, 리포트 구조, 차트 요구, hero 이미지 방향, 리뷰 기준, 완료/차단 조건을 둔다.

### 3.2 `/research`

파일: `.claude/skills/research/SKILL.md`  
출력: `research/<slug>.md`, 필요 시 `output/assets/*latest100.json`, `*analysis100.json`, 수급/가격 원자료 JSON

Research Generator는 plan을 기준으로 ticker, 기간, 주요 뉴스, 공시, 실적, 리스크, 가격 데이터 요구를 확정한다.

현재 규칙:

- plan 없이 research를 만들지 않는다.
- 가격 데이터는 yfinance 일봉(`interval=1d`) 기준이다.
- 관련 종목이 있으면 종목별 최신 뉴스 최소 100건을 수집·분류·분석한다.
- 각 뉴스는 날짜, 매체, 제목, 핵심 이슈, 가격/수급/리스크 해석, URL을 남긴다.
- URL이 없으면 원문 URL을 추측하지 않고 fallback을 명시한다.
- 한국 상장 종목은 가능하면 토스증권 뉴스와 투자자별 매매 동향을 참고한다.

보조 스크립트 `.claude/skills/research/scripts/browse.sh`는 `claude` CLI와 Playwright MCP를 사용해 웹 리서치를 수행하도록 설계되어 있다.

### 3.3 `/draft`

파일: `.claude/skills/draft/SKILL.md`  
출력: `drafts/<slug>.md`

Report Generator는 plan과 research를 모두 읽고 리포트 원고를 만든다.

필수 조건:

- `plan_source`, `research_source`, `ticker`, `period_start`, `period_end` 포함
- plan/research와 ticker·기간 일치
- 5문장 내외 문단 구성
- 숫자와 가격 해석에 검증용 출처 표식
- 투자 권유처럼 보이는 표현 금지
- `References` 존재
- 뉴스 100건이 있으면 최신 뉴스 5건 요약 블록 포함
- 가격 차트는 직접 데이터 배열이 아니라 `price-chart` 블록으로 선언

### 3.4 `/image`

파일: `.claude/skills/image/SKILL.md`  
보조 스크립트:

- `.claude/skills/build/scripts/make-image-prompt-variants.py`
- `.claude/skills/build/scripts/make-image-prompt.py`
- `.claude/skills/build/scripts/select-best-image.py`

Image Generator는 plan, research, draft를 읽고 전체 리포트의 메시지를 hero 이미지로 압축한다.

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

이미지 프롬프트의 현재 원칙은 “Korean stock economic report”용 프리미엄 editorial hero다. 텍스트, 숫자, 티커, 로고, 워터마크, UI 스크린샷은 금지된다.

### 3.5 `/review`

파일: `.claude/skills/review/SKILL.md`  
출력: `reviews/<slug>.md`

Review는 메인 세션이 직접 수행하지 않는다. 실제 검토는 아래 네 관점으로 분리된다.

| 리뷰어 | 방식 | 주요 책임 |
|---|---|---|
| `fact-checker` | Task subagent | ticker·기간·숫자·가격·출처 정합성 |
| `report-designer` | Task subagent | 리포트 구조, 독자 흐름, 차트/hero 연결성 |
| `content-editor` | Task subagent | 문장, 톤, 중복, 가독성, 투자 권유 표현 제거 |
| Codex independent review | `gpt-review.sh` / `gpt-review.ps1` | 논리 비약, plan 누락, blind spot 교차 검토 |

필수 review frontmatter:

```yaml
review_type: separate-session-4way
review_execution: separate_subagent_sessions
reviewers: fact-checker, report-designer, content-editor, codex-independent
```

`status: pass`는 네 리뷰어 모두 빌드 차단 이슈가 없을 때만 가능하다. `needs_fix`이면 generator 단계로 돌아가 수정 후 다시 review를 실행한다.

### 3.6 `/build`

파일: `.claude/skills/build/SKILL.md`  
진입점:

- `.claude/skills/build/scripts/build-html.sh --slug <slug>`
- `.claude/skills/build/scripts/build-html.py --draft drafts/<slug>.md --output output/<slug>.html`

Builder는 검증된 원고와 자산을 HTML로 조립한다. 새 주장을 만들지 않는다.

검증 항목:

- plan/research/draft/review 존재
- review `status: pass`
- review `review_type: separate-session-4way`
- review `review_execution: separate_subagent_sessions`
- selected image JSON과 실제 이미지 파일 존재
- draft frontmatter 필수값 존재
- plan/research/draft의 ticker·기간 일치
- H1 정확히 1개
- 필수 섹션: 개요, 배경, 메커니즘, 영향과 적용
- References 존재
- 본문 footnote 번호 금지
- ticker와 기간이 있으면 yfinance 기반 가격 차트 최소 1개
- 가격 차트 기간 366일 이내
- 차트 날짜 label은 `YYYY-MM-DD` 오름차순
- 모든 차트에 `ariaLabel`

렌더링 특징:

- Chart.js v4 CDN
- Pretendard 폰트 CDN
- `main.report-shell` 통합 리포트 시트
- sticky TOC
- 다크모드 토글
- hero 이미지 1장
- price chart summary cards
- final HTML에서 `[S1]`, `[N1]`, `[T1]`, `[R1]` 같은 검증용 표식 제거
- HTML 메타 generator: `stock-report-harness v1`

## 4. 전용 에이전트

### 4.1 `fact-checker`

파일: `.claude/agents/fact-checker.md`

역할은 근거 체인 검증이다. plan/research/draft 사이의 ticker, 기간, 숫자, 가격 데이터, References, 최신 뉴스 5건 링크, yfinance 조건을 점검한다.

### 4.2 `report-designer`

파일: `.claude/agents/report-designer.md`

역할은 리포트 구조 검증이다. plan의 목표와 대상 독자에 맞는지, 초보자가 이해 가능한 흐름인지, price-chart와 hero 이미지가 리포트 메시지와 연결되는지 확인한다.

### 4.3 `content-editor`

파일: `.claude/agents/content-editor.md`

역할은 문장 품질 검증이다. 중복, 장황함, 톤, 제목/소제목, 면책 문구, 투자 권유처럼 보이는 문장, 최신 뉴스 5건 요약의 자연스러움을 점검한다.

## 5. Hook 기반 가드레일

`.claude/settings.json`은 PreToolUse, Stop, UserPromptSubmit hook을 등록한다.

### 5.1 PreToolUse

- `block-dangerous-bash.sh`  
  `rm -rf /`, `sudo`, 원격 스크립트 pipe 실행, `chmod 777`, 강제 push 등 위험 shell 명령을 차단한다.

- `protect-sensitive-files.sh`  
  `.env`, `.github/workflows`, `.git`, `docs/finance-style-guide.md`, `docs/output-spec.md` 같은 보호 경로 수정을 차단한다.

- `forbid-financial-advice.sh`  
  `drafts/*.md`, `output/*.html`에 투자 권유·수익 보장·도박성 표현이 들어가는 것을 차단한다.

### 5.2 Stop

- `enforce-plan.sh`  
  `research`, `drafts`, `output` 변경 시 선행 plan/research/review/selected-image 계약을 확인한다.

- `review-feedback-loop.sh`  
  `reviews/<slug>.md`가 `needs_fix`인데 generator 산출물이 더 최신이 아니면 종료를 막는다.

- `enforce-citations.sh`  
  변경된 draft에서 면책 문구와 숫자 주장 출처 누락을 1차로 검사한다.

- `remind-review.sh`  
  draft 변경 후 `fact-checker`, `report-designer`, `content-editor`, Codex review 증거 또는 최신 pass review 파일을 요구한다.

- `enforce-memory.sh`  
  memory 파일 변경 시 `scripts/validate_memory.py`를 실행한다.

### 5.3 UserPromptSubmit

- `inject-memory-context.sh`  
  사용자 prompt를 `scripts/memory_context.py`에 전달해 관련 memory topic을 자동 주입한다.

## 6. 보조 스크립트

### 6.1 `scripts/news_latest5.py`

100건 뉴스 JSON에서 최신 5건을 뽑아 markdown/html/json으로 출력한다.

- 입력 구조: list 또는 `body/items/articles/news/data/results`
- 날짜 키: `published_at_utc`, `publishedAt`, `createdAt`, `updatedAt`, `date`
- URL 키: `url`, `link`, `article_url`, `articleUrl`, `original_url`, `canonical_url`, `google_news_link`, `news_url` 등
- fallback: provider 뉴스 목록 URL 또는 제목 기반 Google 검색 URL

### 6.2 `scripts/memory_context.py`

프롬프트 키워드로 memory topic을 선택해 Claude `additionalContext` JSON을 출력한다. 날짜/yfinance, external API, image workflow, pipeline order, build errors, git workflow, guardrails 도메인을 구분한다.

### 6.3 `scripts/validate_memory.py`

`memory/_daily/*.md`와 `memory/topics/*.md` 형식을 검증한다. topic은 고정 6섹션(`상황`, `증상`, `원인`, `해결`, `검증`, `일자`)을 요구한다.

### 6.4 `server.js`

`output/`을 정적 서버로 제공한다. 기본 포트는 3000이고 `PORT` 환경변수로 변경 가능하다.

## 7. 문서와 템플릿

현재 문서 체계:

- `docs/pedagogy.md`: 리포트 5섹션 구성, 가격 차트 원칙, 강조/References 원칙
- `docs/finance-style-guide.md`: 금지 표현, 면책 문구, 수급 데이터, 용어, 숫자, 출처 신뢰도
- `docs/visual-system.md`: 최종 HTML 디자인 토큰, 레이아웃, 컴포넌트, 다크모드, 인쇄/공유
- `docs/output-spec.md`: 최종 HTML 구조, frontmatter, price-chart, hero image, 최신 뉴스 5건, build 검증
- `docs/image-generation-spec.md`: hero 이미지 생성/선택 규칙
- `docs/templates/planning-brief-template.md`: plan 템플릿
- `docs/templates/report-template.md`: draft 템플릿
- `docs/memory-system.md`: memory 기록·검증 규칙

일부 템플릿 파일에는 과거 인코딩 손상 흔적이 남아 있으므로, 실제 동작 계약은 `.claude/skills/*/SKILL.md`와 `build-html.py` 검증 로직을 우선한다.

## 8. 파일 계약 관점의 시스템 상태

| 단계 | 입력 | 출력 | 차단 조건 |
|---|---|---|---|
| Plan | 사용자 요청 | `plan/<slug>.md` | 기간/ticker/차트/리뷰 기준 불명확 |
| Research | plan | `research/<slug>.md`, 원자료 JSON | plan 없음, ticker/기간 미확정, URL/fallback 미기록 |
| Draft | plan + research | `drafts/<slug>.md` | source frontmatter 누락, 출처/면책 누락, price-chart 미사용 |
| Image | plan + research + draft | hero 3종, score, selected JSON | selected image 없음, 리포트 메시지와 불일치 |
| Review | plan + research + draft | `reviews/<slug>.md` | 별도 세션 증거 없음, needs_fix 미해결 |
| Build | 모든 선행 산출물 | `output/<slug>.html`, price chart JSON | pass review 없음, selected image 없음, yfinance/섹션/frontmatter 검증 실패 |

## 9. 현재 예시 산출물

저장소에는 다음 slug의 산출물이 있다.

- `nvidia-recent-4m-2026-05`
- `nvidia-recent-6m-2026-05`
- `samsung-electronics-recent-1y-2026-05`
- `samsung-electronics-recent-30d-2026-05`
- `tesla-recent-6m-2026-05` 일부 research/assets 원자료

이 예시들은 `output/assets/*price-chart-v1.json`, hero 이미지, selected-image JSON, Toss/Google News 원자료 등 현재 계약의 산출물 형태를 보여준다.

## 10. 결론

현재 프로젝트는 “주식 리포트를 빨리 쓰는 프롬프트 묶음”이 아니라, 에이전트 작업을 파일 인터페이스와 hook 검증으로 제어하는 경제리포트 생산 하네스다.

가장 중요한 불변 조건은 다음이다.

- plan 없이 downstream 산출물을 만들지 않는다.
- research 없이 draft를 만들지 않는다.
- selected hero 이미지 없이 build하지 않는다.
- separate-session 4-way pass review 없이 build하지 않는다.
- 가격 차트는 yfinance 일봉으로만 생성한다.
- 최종 HTML은 검증용 인라인 참조 표식을 숨기고 References로만 출처를 정리한다.
- 투자 권유처럼 읽히는 표현은 draft/output 단계에서 차단한다.

따라서 이 시스템의 가치는 생성 속도보다 **재현 가능성, 근거 추적성, 검증 가능성, 금융 표현 안전성**에 있다.
