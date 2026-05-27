---
name: stock-plan
description: Create a stock-report-harness planning brief from a natural-language stock, ETF, or sector request. Use for /stock-plan prompts such as "삼성전자 30일 분석", and whenever Codex must write plan/<slug>.md before stock research, drafting, image, review, or build stages.
---

# Stock Plan Skill

Create `plan/<slug>.md`, the single source of truth for all downstream stock-report-harness stages.

## Procedure

1. Parse the request.
   - Identify topic, audience, ticker/proxy, chart requirement, and requested period.
   - If no period is stated, use the recent 6 calendar months and record this in `assumptions`.
   - If the end date is not stated, use the current local date.
   - Use yfinance symbols: US tickers as-is, Korean KOSPI/KOSDAQ symbols with `.KS`/`.KQ` when known.
2. Create a stable lowercase `slug` in English kebab-case, including subject, period, and year-month, e.g. `samsung-electronics-recent-30d-2026-05`.
3. Write `plan/<slug>.md` with required frontmatter:
   `slug`, `topic`, `request`, `output_type`, `audience`, `ticker`, `period_start`, `period_end`, `chart_required`, `price_data_source`, `price_data_interval`, `created_at`, `assumptions`.
4. Body must include:
   - 요청 해석
   - 이해 목표
   - 리서치 범위
   - 데이터 확인 항목
   - 리포트 구조
   - 차트 요구
   - Hero 이미지 방향
   - 리뷰 기준
   - 완료/차단 조건
5. Do not proceed to research/draft/build in this skill unless the user explicitly asked for multiple stages; `stock-goal` counts as that explicit multi-stage request. If they did, complete the plan first and then invoke the next `/stock-*` stage.

## Constraints

- Do not invent unknown tickers. If uncertain after reasonable lookup, set `ticker: TBD` and add a blocker.
- Keep language Korean by default for Korean user requests.
- Do not include investment recommendations, return guarantees, or trading instructions.
- Preserve folder contracts: planning output always goes under `plan/` even though the command name is `/stock-plan`.

## Completion Report

Report the created plan path, resolved ticker, period, slug, and next command:
`/stock-research <slug>`.

If invoked by `stock-goal`, this report is only an internal checkpoint. Do not stop or wait for the user; continue immediately to `/stock-research <slug>`.
