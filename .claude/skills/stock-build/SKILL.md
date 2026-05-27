---
name: stock-build
description: Build the final stock-report-harness HTML report. Use for /stock-build <slug> only after pass review and selected hero image exist; validates contracts, generates yfinance price chart JSON, renders output/<slug>.html, removes inline source markers from final body, and adds footer investment disclaimer.
---

# Stock Build Skill

Create `output/<slug>.html` from approved artifacts without adding new claims.
The build implementation is deterministic: use `python3 scripts/build_report.py <slug>`
rather than hand-writing HTML.

## Preconditions

Required files must exist:

- `plan/<slug>.md`
- `research/<slug>.md`
- `drafts/<slug>.md`
- `reviews/<slug>.md` with `status: pass`
- `output/assets/<slug>-image-manifest.json` with `status: complete`, `generation_method: codex-cli-imagegen`, and `generated_with`
- `output/assets/<slug>-selected-image.json`
- selected hero PNG referenced by selected-image JSON

If any are missing or review is not pass, stop and route to the required `/stock-*` stage.

## Procedure

1. Run the pre-build contract gate:
   `python3 scripts/validate_report_contract.py <slug>`
   - If it fails, route to the upstream stage named by the error instead of building.
2. Run the deterministic builder:
   `python3 scripts/build_report.py <slug>`
   - The builder validates frontmatter consistency across plan, research, draft, and review.
   - The builder generates/refreshes `output/assets/<slug>-price-chart-v1.json` from actual yfinance daily data for the full requested period.
   - The builder renders Markdown/frontmatter into `output/<slug>.html` using the Toss design system in `design/toss_design.md` (see `sample/skhynix.html` for a reference composition) and removes inline source markers.
3. Confirm the strict post-build gate passed or run it explicitly:
   `python3 scripts/validate_report_contract.py <slug> --require-html --require-price-chart`
4. The generated HTML must:
   - use the Toss-style mobile shell: `max-width: 560px`, sticky app bar, ticker hero card, Pretendard, Toss Blue accent, gray 8px section dividers, and Korean stock color convention (up=red, down=blue)
   - include selected hero image once near the top, styled as a quiet Toss card to satisfy the report asset contract
   - render `price-chart` blocks as accessible Chart.js-compatible charts with Toss line styling and right-side Y axis
   - when the draft/research contains sharp rise/fall event metadata, emphasize those dates in the price chart and render short event cards near the chart
   - render fenced `chart` JSON as charts when present
   - remove inline `[S1]`, `[N1]` markers from final body text
   - keep References section with source details
   - include footer note: educational information only, not investment advice
   - ensure long news links cannot overflow the content column (`overflow-wrap: anywhere` / `word-break: break-word` on article links, list items, and reference URLs)
5. Final checks are enforced by `validate_report_contract.py`:
   - HTML file exists and is non-empty
   - selected image path resolves
   - price chart JSON exists and matches ticker/period
   - no inline source markers remain outside References
   - no new claims were introduced beyond the draft/research
6. After a successful build, start or reuse the local preview server and surface the direct report URL:
   - Preferred command: `node server.js <slug>`
   - If port 3000 is already in use, do not kill unknown processes; report `http://localhost:3000/<slug>.html` if the existing server is reachable, or use `PORT=<free-port> node server.js <slug>` and report that URL.
   - The console/report must include a direct link such as `http://localhost:3000/<slug>.html`.

## Constraints

- Do not build without pass review.
- Do not build without selected hero image.
- Do not build with procedural/Pillow/SVG/placeholder hero provenance.
- Do not use fake prices or placeholder charts.
- Do not add fresh market claims during build; fix research/draft first.

## Completion Report

Report final HTML path, price chart JSON path, selected hero path, preview URL, and validation evidence.
