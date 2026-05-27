---
name: stock-research
description: Produce source-backed research for a stock-report-harness slug. Use for /stock-research <slug> after /stock-plan, including yfinance daily prices, 100 latest news items where relevant, Korean stock Toss Securities news/transaction-status checks, and research/<slug>.md output.
---

# Stock Research Skill

Create `research/<slug>.md` and raw evidence files under `output/assets/` from `plan/<slug>.md`.

## Preconditions

- `plan/<slug>.md` must exist. If missing, stop and tell the user to run `/stock-plan <요청>` first.
- Read the plan frontmatter and preserve `ticker`, `period_start`, `period_end`, `price_data_source`, and `price_data_interval`.

## Procedure

1. Validate ticker and period against the plan.
2. Pull actual daily price data with `yfinance`, `interval=1d`, for the full requested period.
   - Save raw/normalized data to `output/assets/<slug>-price-chart-v1.json` or a clearly named yfinance raw file.
   - Use `YYYY-MM-DD` labels in ascending order.
3. Gather source-backed context:
   - Prefer primary sources: company IR, official newsroom, filings, exchange/central bank data.
   - Use reputable media for events and risks.
   - For Korean listed stocks, use Toss Securities stock news and investor transaction-status if accessible.
4. For stock/ETF/sector requests, collect and classify at least 100 latest relevant news items when feasible.
   - Save raw latest news JSON as `output/assets/<slug>-*-latest100.json`.
   - Save classification/analysis JSON as `output/assets/<slug>-*-analysis100.json`.
   - Do not fabricate article URLs. If an API lacks item URLs, keep a provider/search fallback and mark `url_is_fallback: true`.
5. Write `research/<slug>.md` with frontmatter containing at least:
   `slug`, `title`, `created_at`, `period_start`, `period_end`, `ticker`, `price_data_source`, `price_data_interval`, `plan_source`, `sources`.
6. Body must include:
   - 결론 요약
   - 주가 데이터 메모
   - 핵심 이벤트/메커니즘
   - 뉴스 100건 표 또는 수집 한계와 근거
   - 수급/투자자별 매매 동향 when available
   - 리스크/불확실성
   - References/source markers such as `[S1]`.

## Constraints

- Never use arbitrary or sampled price data.
- Never manipulate nonexistent article URLs.
- Separate facts from inference.
- If external access is blocked, write a `blocked`/limitation section with exact missing data instead of inventing evidence.

## Completion Report

Report `research/<slug>.md`, key raw JSON files, price data row count, news item count, and next command: `/stock-draft <slug>`.

If invoked by `stock-goal`, this report is only an internal checkpoint. Do not stop or wait for the user; continue immediately to `/stock-draft <slug>`.
