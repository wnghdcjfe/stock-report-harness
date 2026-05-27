#!/usr/bin/env python3
"""Deterministically build output/<slug>.html from approved report artifacts.

The builder intentionally performs no research and adds no new market claims. It
only renders the approved draft, refreshes the requested yfinance price chart,
removes inline verification markers from the final body, inserts the selected
hero image, and runs the same contract validator used by review/build gates.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from report_contract_lib import (
    ASSET_DIR,
    OUTPUT_DIR,
    PRICE_CHART_FENCE_RE,
    ROOT,
    artifact_paths,
    frontmatter_value,
    html_attr,
    html_text,
    parse_key_value_block,
    price_chart_blocks,
    read_markdown,
    rel,
    selected_image_path,
    strip_source_markers,
)
from validate_report_contract import print_result, validate_contract

CHART_FENCE_RE = re.compile(r"```chart\s*\n(?P<body>.*?)\n```", re.DOTALL)
STAT_CARD_RE = re.compile(r"::stat-card\s*\n(?P<body>.*?)\n::", re.DOTALL)
SOURCE_MARKER_PREFIX_RE = re.compile(r"^\s*-\s+(?:\[(?:S|N|P)\d+\]\s*)+", re.MULTILINE)
INITIAL_H1_RE = re.compile(r"^#(?!#)\s+.+?\s*$\n?", re.MULTILINE)
H2_HTML_RE = re.compile(r"<h2>(?P<title>.*?)</h2>")
DISCLAIMER_SECTION_RE = re.compile(
    r"^##\s*(?:⚠️\s*)?(?:면책|투자\s*판단\s*면책|투자\s*유의(?:사항)?|유의사항)\s*$.*?(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)

DEFAULT_DISCLAIMER = (
    "이 리포트는 교육 및 정보 제공 목적의 시장 해설입니다. 특정 종목의 매수·매도를 권유하지 "
    "않으며 투자 자문이 아닙니다. 모든 투자 판단과 그 결과에 대한 책임은 투자자 본인에게 있습니다."
)

SECTION_IDS = {
    "개요": "overview",
    "배경": "background",
    "메커니즘": "mechanism",
    "최신 뉴스 5건 요약": "latest-news-5",
    "영향과 적용": "impact",
    "핵심 정리": "key-takeaways",
    "References": "references",
}


def parse_date(value: str, key: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"{key} must be YYYY-MM-DD, got {value!r}") from exc


def assert_price_period(period_start: str, period_end: str) -> tuple[date, date]:
    start = parse_date(period_start, "period_start")
    end = parse_date(period_end, "period_end")
    if end < start:
        raise SystemExit(f"period_end must be >= period_start: {period_start}~{period_end}")
    if (end - start).days > 366:
        raise SystemExit("price chart period exceeds 366 days; narrow the plan period before build")
    return start, end


def normalize_number(value: Any) -> float | int | None:
    if value is None:
        return None
    try:
        if hasattr(value, "item"):
            value = value.item()
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    if number.is_integer():
        return int(number)
    return round(number, 6)


def flatten_yfinance_frame(df: Any, ticker: str) -> Any:
    # yfinance often returns a MultiIndex even for one ticker:
    # level 0 = Price, level 1 = Ticker. Collapse to Price names.
    try:
        import pandas as pd  # noqa: F401  # type: ignore
    except Exception:
        return df

    if getattr(df, "empty", True):
        return df
    columns = getattr(df, "columns", None)
    if getattr(columns, "nlevels", 1) > 1:
        tickers = list(columns.get_level_values(-1).unique())
        if ticker in tickers:
            try:
                return df.xs(ticker, axis=1, level=-1)
            except Exception:
                pass
        df = df.copy()
        df.columns = columns.get_level_values(0)
    return df


def download_price_rows(ticker: str, period_start: str, period_end: str, interval: str, field: str) -> list[dict[str, Any]]:
    start, end = assert_price_period(period_start, period_end)
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:
        raise SystemExit("yfinance is required. Install with: pip install -r requirements.txt") from exc

    # yfinance's end date is exclusive, so add one calendar day to include period_end.
    df = yf.download(
        ticker,
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        interval=interval,
        progress=False,
        auto_adjust=False,
        timeout=30,
    )
    df = flatten_yfinance_frame(df, ticker)
    if getattr(df, "empty", True):
        raise SystemExit(f"yfinance returned no {interval} rows for {ticker} {period_start}~{period_end}")

    rows: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        row_date = idx.date() if hasattr(idx, "date") else parse_date(str(idx)[:10], "price row date")
        if row_date < start or row_date > end:
            continue
        record = {
            "date": row_date.isoformat(),
            "open": normalize_number(row.get("Open")),
            "high": normalize_number(row.get("High")),
            "low": normalize_number(row.get("Low")),
            "close": normalize_number(row.get("Close")),
            "adj_close": normalize_number(row.get("Adj Close")),
            "volume": normalize_number(row.get("Volume")),
        }
        field_key = field.lower().replace(" ", "_")
        record["value"] = record.get(field_key) if field_key in record else record.get("close")
        if record["value"] is not None:
            rows.append(record)

    if not rows:
        raise SystemExit(f"No usable {field} values for {ticker} {period_start}~{period_end}")
    rows.sort(key=lambda item: item["date"])
    return rows


def load_existing_price_rows(path: Path, ticker: str, period_start: str, period_end: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"existing price chart is not an object: {rel(path)}")
    expected = {"ticker": ticker, "period_start": period_start, "period_end": period_end}
    for key, value in expected.items():
        actual = str(payload.get(key) or "")
        if actual != value:
            raise SystemExit(f"existing price chart `{key}` mismatch: {actual!r} != {value!r}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SystemExit(f"existing price chart has no rows: {rel(path)}")
    return [row for row in rows if isinstance(row, dict)]


def currency_symbol(currency: str) -> str:
    return {"USD": "$", "KRW": "₩", "JPY": "¥", "EUR": "€"}.get(currency.upper(), "")


def format_value(value: Any, currency: str = "") -> str:
    number = normalize_number(value)
    if number is None:
        return "-"
    symbol = currency_symbol(currency)
    if isinstance(number, int):
        return f"{symbol}{number:,}"
    return f"{symbol}{number:,.2f}"


def build_price_chart_payload(
    *,
    slug: str,
    ticker: str,
    period_start: str,
    period_end: str,
    block: dict[str, str],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    field = block.get("field") or "Close"
    interval = block.get("interval") or "1d"
    currency = block.get("currency") or ""
    title = block.get("title") or f"{ticker} {period_start}~{period_end} {field}"
    aria_label = block.get("aria_label") or block.get("ariaLabel") or f"{ticker} {period_start}부터 {period_end}까지 {field} 차트"
    labels = [str(row["date"]) for row in rows]
    data = [row.get("value") for row in rows]
    chart = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": data,
                    "borderColor": "#2563eb",
                    "backgroundColor": "rgba(37,99,235,0.14)",
                    "fill": True,
                    "tension": 0.2,
                    "pointRadius": 0,
                    "pointHoverRadius": 3,
                    "borderWidth": 2,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "interaction": {"mode": "index", "intersect": False},
            "plugins": {"legend": {"display": False}, "tooltip": {"displayColors": False}},
            "scales": {
                "x": {"grid": {"display": False}},
                "y": {"grid": {"color": "rgba(115,114,108,0.14)"}},
            },
        },
    }
    return {
        "slug": slug,
        "ticker": ticker,
        "period_start": period_start,
        "period_end": period_end,
        "interval": interval,
        "field": field,
        "currency": currency,
        "source": "yfinance",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ariaLabel": aria_label,
        "title": title,
        "rows": rows,
        "chart": chart,
    }


def write_price_charts(
    *,
    slug: str,
    ticker: str,
    period_start: str,
    period_end: str,
    draft_blocks: list[dict[str, str]],
    reuse_existing_price_chart: bool,
) -> list[dict[str, Any]]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    payloads: list[dict[str, Any]] = []
    if not draft_blocks:
        raise SystemExit("draft has no price-chart block")

    for index, block in enumerate(draft_blocks, start=1):
        interval = block.get("interval") or "1d"
        field = block.get("field") or "Close"
        path = ASSET_DIR / f"{slug}-price-chart-v{index}.json"
        if reuse_existing_price_chart and path.is_file():
            rows = load_existing_price_rows(path, ticker, period_start, period_end)
        else:
            rows = download_price_rows(ticker, period_start, period_end, interval, field)
        payload = build_price_chart_payload(
            slug=slug,
            ticker=ticker,
            period_start=period_start,
            period_end=period_end,
            block=block,
            rows=rows,
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payloads.append(payload)
    return payloads


def render_summary_cards(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return ""
    parts = ["<div class=\"chart-summary\">"]
    for card in cards:
        tone = str(card.get("tone") or "neutral")
        label = html_text(card.get("label") or "")
        value = html_text(card.get("value") or "")
        parts.append(
            f'<div class="chart-summary-card chart-summary-card--{html_attr(tone)}">'
            f'<div class="chart-summary-card__label">{label}</div>'
            f'<div class="chart-summary-card__value">{value}</div>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def price_summary_cards(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict) and row.get("value") is not None]
    if not rows:
        return []
    currency = str(payload.get("currency") or "")
    start_value = rows[0]["value"]
    end_value = rows[-1]["value"]
    max_value = max(row["value"] for row in rows)
    change_pct = None
    try:
        change_pct = ((float(end_value) / float(start_value)) - 1.0) * 100
    except Exception:
        pass
    tone = "neutral"
    change_label = "-"
    if change_pct is not None:
        tone = "up" if change_pct >= 0 else "down"
        change_label = f"{change_pct:+.2f}%"
    return [
        {"label": "기간 수익률", "value": change_label, "tone": tone},
        {"label": "시작값", "value": format_value(start_value, currency), "tone": "neutral"},
        {"label": "최고값", "value": format_value(max_value, currency), "tone": "up"},
        {"label": "종료값", "value": format_value(end_value, currency), "tone": tone},
    ]


def render_chart_container(chart_id: str, aria_label: str, summary_cards: list[dict[str, Any]]) -> str:
    summary = render_summary_cards(summary_cards)
    return (
        f'{summary}<div class="chart-container"><canvas id="{html_attr(chart_id)}" '
        f'aria-label="{html_attr(aria_label)}"></canvas>'
        f'<p class="sr-only">{html_text(aria_label)}</p></div>'
    )


def sanitize_chart_config(config: dict[str, Any]) -> dict[str, Any]:
    config = dict(config)
    config.pop("summaryCards", None)
    config.pop("ariaLabel", None)
    config.pop("aria_label", None)
    return config


def render_stat_card(match: re.Match[str]) -> str:
    data = parse_key_value_block(match.group("body"))
    tone = data.get("tone") or "neutral"
    return (
        f'<div class="stat-card stat-card--{html_attr(tone)}">'
        f'<div class="stat-card__label">{html_text(data.get("label", ""))}</div>'
        f'<div class="stat-card__title">{html_text(data.get("title", ""))}</div>'
        f'<div class="stat-card__value">{html_text(data.get("value", ""))}</div>'
        f'<div class="stat-card__compare">{html_text(data.get("compare", ""))}</div>'
        "</div>"
    )


def render_markdown(markdown_text: str) -> str:
    try:
        import markdown  # type: ignore

        return markdown.markdown(
            markdown_text,
            extensions=["tables", "sane_lists"],
            output_format="html5",
        )
    except Exception:
        try:
            from markdown_it import MarkdownIt  # type: ignore

            md = MarkdownIt("commonmark", {"html": True, "linkify": False})
            try:
                md.enable(["table", "strikethrough"])
            except Exception:
                pass
            return md.render(markdown_text)
        except Exception:
            pass

    # Minimal fallback for environments that have not installed requirements yet.
    lines: list[str] = []
    in_list = False
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            if in_list:
                lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("## "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h2>{html_text(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h3>{html_text(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{html_text(line[2:].strip())}</li>")
        elif line.startswith("<"):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(line)
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<p>{html_text(line)}</p>")
    if in_list:
        lines.append("</ul>")
    return "\n".join(lines)

def slugify_heading(title_html: str) -> str:
    text = re.sub(r"<[^>]+>", "", title_html)
    text = html.unescape(text).strip()
    if text in SECTION_IDS:
        return SECTION_IDS[text]
    slug = re.sub(r"[^0-9A-Za-z가-힣_-]+", "-", text).strip("-")
    return slug or "section"


def wrap_h2_sections(rendered_html: str) -> tuple[str, list[tuple[str, str]]]:
    matches = list(H2_HTML_RE.finditer(rendered_html))
    if not matches:
        return rendered_html, []
    parts: list[str] = []
    toc: list[tuple[str, str]] = []
    leading = rendered_html[: matches[0].start()].strip()
    if leading:
        parts.append(f'<div class="lead-content">{leading}</div>')
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rendered_html)
        title_html = match.group("title")
        section_id = slugify_heading(title_html)
        toc.append((section_id, re.sub(r"<[^>]+>", "", html.unescape(title_html))))
        section_body = rendered_html[start:end].strip()
        parts.append(f'<section id="{html_attr(section_id)}"><h2>{title_html}</h2>{section_body}</section>')
    return "\n".join(parts), toc


def transform_body(body: str, price_payloads: list[dict[str, Any]]) -> tuple[str, list[tuple[str, dict[str, Any]]], list[tuple[str, str]]]:
    chart_scripts: list[tuple[str, dict[str, Any]]] = []
    price_iter = iter(price_payloads)
    chart_index = 0

    # Remove the draft's title H1; the HTML header owns the single final H1.
    body = INITIAL_H1_RE.sub("", body, count=1).strip()
    # Output spec renders any draft disclaimer as the single footer note.
    body = DISCLAIMER_SECTION_RE.sub("", body).strip()
    # Keep source details but remove bracketed inline verification markers globally.
    body = SOURCE_MARKER_PREFIX_RE.sub("- ", body)
    body = strip_source_markers(body)
    body = STAT_CARD_RE.sub(render_stat_card, body)

    def replace_price_chart(_match: re.Match[str]) -> str:
        nonlocal chart_index
        try:
            payload = next(price_iter)
        except StopIteration:
            raise SystemExit("price-chart block count changed during render")
        chart_id = f"chart-{chart_index}"
        chart_index += 1
        chart_scripts.append((chart_id, payload["chart"]))
        return render_chart_container(chart_id, str(payload.get("ariaLabel") or "가격 차트"), price_summary_cards(payload))

    def replace_chart(match: re.Match[str]) -> str:
        nonlocal chart_index
        raw = match.group("body")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid fenced chart JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise SystemExit("fenced chart JSON must be an object")
        aria_label = str(payload.get("ariaLabel") or payload.get("aria_label") or payload.get("title") or "차트")
        summary_cards = payload.get("summaryCards") if isinstance(payload.get("summaryCards"), list) else []
        chart_id = f"chart-{chart_index}"
        chart_index += 1
        chart_scripts.append((chart_id, sanitize_chart_config(payload)))
        return render_chart_container(chart_id, aria_label, summary_cards)

    body = PRICE_CHART_FENCE_RE.sub(replace_price_chart, body)
    body = CHART_FENCE_RE.sub(replace_chart, body)
    rendered = render_markdown(body)
    wrapped, toc = wrap_h2_sections(rendered)
    return wrapped, chart_scripts, toc


def render_toc(toc: list[tuple[str, str]]) -> str:
    if not toc:
        return ""
    links = " ".join(f'<a href="#{html_attr(section_id)}">{html_text(title)}</a>' for section_id, title in toc)
    return f'<nav class="toc" aria-label="목차">{links}</nav>'


def css() -> str:
    return """
:root {
  --bg-base: #ffffff; --bg-surface: #f7f7f8; --bg-elevated: #ffffff;
  --text-strong: #18181b; --text-base: #3f3f46; --text-muted: #71717a;
  --accent: #2563eb; --up: #16a34a; --down: #dc2626; --border: #e4e4e7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg-base: #0a0a0a; --bg-surface: #18181b; --bg-elevated: #27272a;
    --text-strong: #fafafa; --text-base: #d4d4d8; --text-muted: #a1a1aa;
    --accent: #60a5fa; --up: #4ade80; --down: #f87171; --border: #3f3f46;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg-surface); color: var(--text-base); font-family: "Pretendard Variable", "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif; font-size: 16px; line-height: 1.7; -webkit-font-smoothing: antialiased; }
main.report-shell { max-width: 840px; margin: 32px auto 96px; padding: 0 36px 64px; background: var(--bg-base); border: 1px solid var(--border); border-radius: 28px; box-shadow: 0 28px 80px rgba(24, 24, 27, 0.08); }
h1 { font-size: clamp(30px, 5vw, 44px); line-height: 1.18; font-weight: 800; letter-spacing: -0.035em; color: var(--text-strong); margin: 0; }
h2 { font-size: 25px; color: var(--text-strong); letter-spacing: -0.02em; margin: 0 0 18px; }
h3 { font-size: 19px; color: var(--text-strong); margin: 30px 0 10px; }
a { color: var(--accent); text-decoration-thickness: .08em; text-underline-offset: .18em; overflow-wrap: anywhere; word-break: break-word; }
ul, ol { padding-left: 1.35rem; }
li, p, td, th, code, pre { overflow-wrap: anywhere; word-break: break-word; }
.report-header { padding: 46px 0 28px; border-bottom: 1px solid var(--border); }
.subtitle { margin: 10px 0 0; color: var(--text-muted); font-size: 18px; }
.report-meta { display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; }
.report-meta span { border:1px solid var(--border); color: var(--text-muted); border-radius:999px; padding:4px 10px; font-size:13px; background: var(--bg-surface); }
.hero-image { margin: 30px 0 0; border-radius: 22px; overflow: hidden; background: var(--bg-surface); border: 1px solid var(--border); box-shadow: 0 20px 60px rgba(0,0,0,0.06); }
.hero-image img { display: block; width: 100%; height: auto; aspect-ratio: 16/9; object-fit: cover; }
.toc { display:flex; flex-wrap:wrap; gap:8px; padding:18px 0 0; }
.toc a { border:1px solid var(--border); border-radius:999px; padding:5px 10px; font-size:13px; color:var(--text-muted); text-decoration:none; }
.lead-content { padding: 26px 0 0; color: var(--text-muted); font-size: 18px; }
section { padding: 50px 0 0; margin: 0; border-top: 1px solid var(--border); }
.lead-content + section, .toc + section { margin-top: 28px; }
section > h2 { display:flex; align-items:center; gap:10px; }
section > h2::before { content:""; display:inline-block; width:4px; height:1.05em; border-radius:999px; background:var(--accent); }
blockquote { margin: 22px 0; padding: 16px 18px; border-left: 4px solid var(--accent); background: var(--bg-surface); color: var(--text-strong); border-radius: 0 14px 14px 0; }
.stat-card { margin: 20px 0; padding: 18px; border-radius: 18px; border: 1px solid var(--border); background: var(--bg-elevated); }
.stat-card__label, .stat-card__compare { color: var(--text-muted); font-size: 13px; }
.stat-card__title { color: var(--text-strong); font-weight: 700; }
.stat-card__value { margin: 5px 0; font-size: 26px; font-weight: 800; color: var(--text-strong); }
.stat-card--up .stat-card__value, .chart-summary-card--up .chart-summary-card__value { color: var(--up); }
.stat-card--down .stat-card__value, .chart-summary-card--down .chart-summary-card__value { color: var(--down); }
.chart-summary { display:flex; gap:12px; margin:22px 0 12px; flex-wrap:wrap; }
.chart-summary-card { flex:1 1 130px; min-width:130px; padding:12px; background:var(--bg-surface); border:1px solid var(--border); border-radius:14px; }
.chart-summary-card__label { font-size:12px; color:var(--text-muted); margin-bottom:3px; }
.chart-summary-card__value { font-size:20px; font-weight:800; color:var(--text-strong); font-variant-numeric: tabular-nums; }
.chart-container { margin: 16px 0 24px; padding: 16px; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 16px; min-height: 360px; }
.chart-container canvas { width: 100% !important; height: 320px !important; }
table { width:100%; border-collapse: collapse; display:block; overflow-x:auto; }
th, td { border-bottom: 1px solid var(--border); padding: 8px; text-align:left; }
.word-cloud { display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; padding:18px; border:1px solid var(--border); border-radius:18px; background:var(--bg-surface); }
.word-cloud__term { color: var(--text-strong); line-height:1.1; }
footer { margin-top:54px; padding-top:22px; border-top:1px solid var(--border); color:var(--text-muted); font-size:13px; }
.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; }
@media (max-width: 720px) { main.report-shell { margin:0; border-radius:0; border-left:0; border-right:0; padding:0 20px 48px; } .report-header { padding-top:34px; } }
""".strip()


def render_html_document(
    *,
    slug: str,
    draft_fm: dict[str, Any],
    body_html: str,
    toc: list[tuple[str, str]],
    selected_image: Path,
    chart_scripts: list[tuple[str, dict[str, Any]]],
) -> str:
    title = frontmatter_value(draft_fm, "title") or slug
    subtitle = frontmatter_value(draft_fm, "subtitle")
    ticker = frontmatter_value(draft_fm, "ticker")
    period_start = frontmatter_value(draft_fm, "period_start")
    period_end = frontmatter_value(draft_fm, "period_end")
    created_at = frontmatter_value(draft_fm, "created_at")
    hero_src = f"assets/{selected_image.name}"
    scripts = "\n".join(
        f'new Chart(document.getElementById({json.dumps(chart_id)}), {json.dumps(config, ensure_ascii=False)});'
        for chart_id, config in chart_scripts
    )
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="stock-report-harness deterministic-builder">
<meta name="report-slug" content="{html_attr(slug)}">
<meta name="generated-at" content="{html_attr(generated_at)}">
<title>{html_text(title)}</title>
<meta property="og:title" content="{html_attr(title)}">
<meta property="og:description" content="{html_attr(subtitle)}">
<meta property="og:type" content="article">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>{css()}</style>
</head>
<body>
<main class="report-shell">
  <header class="report-header">
    <h1>{html_text(title)}</h1>
    {f'<p class="subtitle">{html_text(subtitle)}</p>' if subtitle else ''}
    <p class="report-meta"><span>{html_text(ticker)}</span><span>{html_text(period_start)} ~ {html_text(period_end)}</span>{f'<span>작성일 {html_text(created_at)}</span>' if created_at else ''}</p>
    <figure class="hero-image"><img src="{html_attr(hero_src)}" alt="{html_attr(title)} hero image" loading="eager"></figure>
    {render_toc(toc)}
  </header>
  {body_html}
  <footer id="disclaimer" aria-label="투자 유의사항"><p>{html_text(DEFAULT_DISCLAIMER)}</p></footer>
</main>
<script>
Chart.defaults.font.family = 'Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif';
{scripts}
</script>
</body>
</html>
"""


def build_report(slug: str, *, reuse_existing_price_chart: bool = False) -> tuple[Path, list[Path], Path]:
    paths = artifact_paths(slug)
    precheck = validate_contract(
        slug,
        require_html=False,
        require_price_chart=False,
        check_html_if_present=False,
        check_price_chart_if_present=False,
    )
    blocking = [error for error in precheck.errors]
    if blocking:
        print_result(precheck)
        raise SystemExit("Cannot build until pre-build contract errors are fixed")

    _plan_fm, _plan_body, _plan_raw, _plan_text = read_markdown(paths.plan)
    _research_fm, _research_body, _research_raw, _research_text = read_markdown(paths.research)
    draft_fm, draft_body, _draft_raw, _draft_text = read_markdown(paths.draft)
    image_path, _image_payload = selected_image_path(slug)
    if image_path is None or not image_path.is_file():
        raise SystemExit(f"selected hero image missing for {slug}")

    ticker = frontmatter_value(draft_fm, "ticker")
    period_start = frontmatter_value(draft_fm, "period_start")
    period_end = frontmatter_value(draft_fm, "period_end")
    blocks = price_chart_blocks(draft_body)
    price_payloads = write_price_charts(
        slug=slug,
        ticker=ticker,
        period_start=period_start,
        period_end=period_end,
        draft_blocks=blocks,
        reuse_existing_price_chart=reuse_existing_price_chart,
    )
    body_html, chart_scripts, toc = transform_body(draft_body, price_payloads)
    html_doc = render_html_document(
        slug=slug,
        draft_fm=draft_fm,
        body_html=body_html,
        toc=toc,
        selected_image=image_path,
        chart_scripts=chart_scripts,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths.html.write_text(html_doc, encoding="utf-8")

    postcheck = validate_contract(slug, require_html=True, require_price_chart=True)
    print_result(postcheck)
    if not postcheck.ok:
        raise SystemExit("Build produced artifacts that failed contract validation")

    price_paths = [ASSET_DIR / f"{slug}-price-chart-v{idx}.json" for idx in range(1, len(price_payloads) + 1)]
    return paths.html, price_paths, image_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument(
        "--reuse-existing-price-chart",
        action="store_true",
        help="Use an already generated matching yfinance price chart JSON instead of downloading. Intended for offline smoke tests only.",
    )
    args = parser.parse_args(argv)

    html_path, price_paths, image_path = build_report(args.slug, reuse_existing_price_chart=args.reuse_existing_price_chart)
    print("Build complete")
    print(f"HTML: {rel(html_path)}")
    print("Price chart JSON:")
    for path in price_paths:
        print(f"- {rel(path)}")
    print(f"Selected hero: {rel(image_path)}")
    print(f"Preview: http://localhost:3000/{html_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
