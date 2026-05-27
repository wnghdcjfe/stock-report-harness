---
name: stock-review
description: Run the stock-report-harness 4-way review gate. Use for /stock-review <slug> after plan, research, draft, and selected hero image exist; writes reviews/<slug>.md with pass, needs_fix, or blocked and separate-session reviewer metadata.
---

# Stock Review Skill

Create `reviews/<slug>.md` as the review gate before build.

## Preconditions

- Required files: `plan/<slug>.md`, `research/<slug>.md`, `drafts/<slug>.md`.
- Required image files: `output/assets/<slug>-selected-image.json` and the selected PNG.

## Procedure

1. Run four review perspectives, preferably in separate Task/subagent sessions:
   - `fact-checker`: ticker, dates, numbers, sources, price data, news links.
   - `report-designer`: flow, chart/hero fit, readability, section completeness.
   - `content-editor`: Korean style, clarity, duplication, no investment advice.
   - `codex-independent` or equivalent: blind-spot review of plan/research/draft/build requirements.
2. Verify invariants:
   - plan/research/draft ticker and period match.
   - Draft has exactly one H1 and required sections.
   - Draft uses `price-chart` block instead of embedded price arrays.
   - References exist and factual claims have source markers.
   - Selected hero image exists.
   - No prohibited investment-advice wording.
3. Write `reviews/<slug>.md` frontmatter:
   `slug`, `status`, `created_at` or `reviewed_at`, `plan_source`, `research_source`, `draft_source`, `review_type: separate-session-4way`, `review_execution: separate_subagent_sessions`, `reviewers`.
4. Set status:
   - `pass` only if build can proceed.
   - `needs_fix` if generator stages can fix issues.
   - `blocked` only for repeated identical blockers or external data/authority limitations.
5. Run the contract validator after writing the review:
   `python3 scripts/validate_report_contract.py <slug>`
   - If validation fails, change `status` to `needs_fix` unless the issue meets the blocked criteria.
   - Include validator errors in the review's fix list.

## Feedback Loop

If `needs_fix`, list exact upstream stage and file to change. Do not build until review status is `pass`.

## Completion Report

Report review status, major issues if any, and next command: `/stock-build <slug>` only when status is `pass`.
