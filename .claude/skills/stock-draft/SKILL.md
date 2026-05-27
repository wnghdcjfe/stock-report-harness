---
name: stock-draft
description: Draft an educational Korean stock-report-harness article from plan/<slug>.md and research/<slug>.md. Use for /stock-draft <slug>, creating drafts/<slug>.md with required sections, price-chart block, References, source markers, and no investment advice.
---

# Stock Draft Skill

Create `drafts/<slug>.md` from the corresponding plan and research.

## Preconditions

- `plan/<slug>.md` and `research/<slug>.md` must exist.
- Use research as the factual boundary; do not add new claims that are not sourced there.

## Procedure

1. Read plan and research; verify `ticker`, `period_start`, and `period_end` match.
2. Write `drafts/<slug>.md` with frontmatter containing at least:
   `slug`, `title`, `subtitle`, `ticker`, `period_start`, `period_end`, `level`, `duration_minutes`, `created_at`, `plan_source`, `research_source`.
3. Include exactly one H1.
4. Required sections:
   - `## 개요`
   - `## 배경`
   - `## 메커니즘`
   - `## 최신 뉴스 5건 요약` when 100-news data exists
   - `## 영향과 적용`
   - `## References`
   - 투자 판단 면책/주의 문구
5. Declare price charts with a fenced `price-chart` block only; do not paste price arrays into prose.
6. Keep source markers such as `[S1]`, `[N1]` in the draft for review/build verification.
7. If adding charts other than price, include valid JSON in fenced `chart` blocks and an `ariaLabel`.
8. For U.S. or other overseas stocks, do not add a separate Korean-style `수급과 투자자 구도` section unless the user explicitly requested it. Korean listed stocks should still include 개인·외국인·기관 수급 when available.
9. In the overview price-chart discussion, identify the largest sharp rise and sharp fall in the requested period, perform web/source lookup for the historical events around those dates, and summarize the event next to the chart with source markers. Do not infer event causality without source support.

## Style and Safety

- Korean, educational, beginner-friendly unless plan says otherwise.
- State uncertainty and risk without trading instructions.
- Avoid “사세요/팔아야/보장/확실” style investment-advice wording.
- Use concise paragraphs and explain mechanisms: what happened, why it mattered, what to watch.

## Completion Report

Report `drafts/<slug>.md`, H1 title, required sections present, and next command: `/stock-image <slug>`.
