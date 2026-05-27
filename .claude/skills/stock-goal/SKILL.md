---
name: stock-goal
description: "End-to-end stock report pipeline. '삼성전자 30일 분석' 같은 자연어 요청 하나로 plan → research → draft → image → review → build 전체를 자동 실행해 output/<slug>.html을 생성한다."
---

# Stock Goal Skill

자연어 요청 하나로 stock-report-harness 전체 파이프라인을 순차 실행해 최종 HTML 리포트를 생성한다.

## Pipeline

```
plan → research → draft → image → review → build
```

각 단계는 해당 `/stock-*` 스킬의 계약을 그대로 따른다.
실패 시 해당 단계에서 멈추고 사용자에게 상태를 보고한다.

## Procedure

### Stage 1: Plan

1. 요청을 파싱한다 (종목/ETF/섹터, 기간, 대상 독자).
2. `/stock-plan` 스킬 계약에 따라 `plan/<slug>.md`를 작성한다.
3. slug를 확정하고 이후 모든 단계에서 동일 slug를 사용한다.

### Stage 2: Research

1. `plan/<slug>.md`가 존재하는지 확인한다.
2. `/stock-research` 스킬 계약에 따라 실행한다.
   - yfinance 일봉 가격 데이터 수집
   - 뉴스 최소 100건 수집·분류
   - `research/<slug>.md` 및 `output/assets/` 원자료 생성
3. 가격 데이터가 조회 불가하면 `blocked`로 보고하고 멈춘다.

### Stage 3: Draft

1. `plan/<slug>.md`와 `research/<slug>.md`가 존재하는지 확인한다.
2. `/stock-draft` 스킬 계약에 따라 `drafts/<slug>.md`를 작성한다.
   - 필수 섹션: 개요, 배경, 메커니즘, 영향과 적용, References
   - price-chart 블록 선언, 투자 권유 금지

### Stage 4: Image

1. plan, research, draft가 모두 존재하는지 확인한다.
2. `/stock-image` 스킬 계약에 따라 hero 이미지 3장을 생성한다.
   - 프롬프트 3개 → PNG 3장 → 스코어링 → 1장 선택
   - `output/assets/<slug>-selected-image.json` 생성
3. 이미지 생성 도구가 없으면 프롬프트만 작성하고 `blocked`로 보고한다.

### Stage 5: Review

1. plan, research, draft, selected image가 모두 존재하는지 확인한다.
2. `/stock-review` 스킬 계약에 따라 4-way review를 실행한다.
   - fact-checker, report-designer, content-editor, codex-independent
3. `reviews/<slug>.md`에 결과를 기록한다.
4. `needs_fix`이면 해당 단계로 돌아가 수정 후 재리뷰한다 (최대 3회).
5. `blocked`이면 사용자에게 보고하고 멈춘다.

### Stage 6: Build

1. review `status: pass`인지 확인한다.
2. `/stock-build` 스킬 계약에 따라 `output/<slug>.html`을 생성한다.
   - yfinance 실데이터 차트, hero 이미지 삽입, 인라인 마커 제거, footer 면책 문구
3. 로컬 프리뷰 서버를 시작하고 URL을 보고한다.

## Execution Rules

- 각 단계는 반드시 선행 산출물이 존재해야 시작한다.
- 단계 간 `slug`, `ticker`, `period_start`, `period_end`가 일관되어야 한다.
- review에서 `needs_fix`가 나오면 fix → re-review 루프를 최대 3회 시도한다.
- 동일 차단 이슈가 3회 반복되면 `blocked`로 전환하고 멈춘다.
- 각 단계 완료 시 진행 상황을 간략히 보고한다.

## Constraints

- AGENTS.md의 모든 계약과 금지 사항을 준수한다.
- 임의 가격 데이터, 조작한 URL, 투자 권유 표현을 사용하지 않는다.
- 각 `/stock-*` 스킬의 산출물 경로와 포맷 계약을 그대로 따른다.

## Completion Report

최종 보고에 포함할 항목:
- 생성된 전체 산출물 목록 (plan, research, draft, images, review, html)
- 최종 HTML 경로: `output/<slug>.html`
- 프리뷰 URL
- 파이프라인 중 발생한 이슈 요약 (있는 경우)
