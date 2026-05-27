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


def sanitize_chart_config(config: dict[str, Any]) -> dict[str, Any]:
    config = dict(config)
    config.pop("summaryCards", None)
    config.pop("ariaLabel", None)
    config.pop("aria_label", None)
    return config


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


# Toss design renderer overrides -------------------------------------------------
# The stock-build stage renders with design/toss_design.md as the canonical visual
# system. The functions below intentionally override the generic renderer above so
# older helpers remain available while the final HTML follows the Toss mobile shell.

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
        "currency": currency,
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": data,
                    "borderColor": "#3182F6",
                    "backgroundColor": "rgba(49,130,246,0.18)",
                    "fill": True,
                    "tension": 0.28,
                    "pointRadius": 0,
                    "pointHitRadius": 6,
                    "pointHoverRadius": 5,
                    "pointHoverBackgroundColor": "#3182F6",
                    "pointHoverBorderColor": "#FFFFFF",
                    "pointHoverBorderWidth": 2,
                    "borderWidth": 2.2,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "interaction": {"mode": "index", "intersect": False},
            "plugins": {
                "legend": {"display": False},
                "tooltip": {
                    "backgroundColor": "#191F28",
                    "titleColor": "#B0B8C1",
                    "bodyColor": "#FFFFFF",
                    "displayColors": False,
                    "padding": 10,
                    "cornerRadius": 8,
                    "titleFont": {"size": 11, "weight": "normal"},
                    "bodyFont": {"size": 13, "weight": "bold"},
                },
            },
            "scales": {
                "x": {
                    "ticks": {"maxTicksLimit": 6, "font": {"size": 10, "family": "Pretendard"}, "color": "#8B95A1"},
                    "grid": {"display": False},
                    "border": {"display": False},
                },
                "y": {
                    "position": "right",
                    "ticks": {"font": {"size": 10, "family": "Pretendard"}, "color": "#8B95A1", "padding": 4},
                    "grid": {"color": "#F2F4F6", "drawTicks": False},
                    "border": {"display": False},
                },
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


def render_summary_cards(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return ""
    parts = ['<div class="stat-grid chart-summary">']
    for card in cards:
        tone = str(card.get("tone") or "neutral")
        parts.append(
            f'<div class="stat-card chart-summary-card stat-card--{html_attr(tone)} chart-summary-card--{html_attr(tone)}">'
            f'<div class="stat-card__label chart-summary-card__label">{html_text(card.get("label") or "")}</div>'
            f'<div class="stat-card__value chart-summary-card__value">{html_text(card.get("value") or "")}</div>'
            '</div>'
        )
    parts.append('</div>')
    return ''.join(parts)


def render_chart_container(chart_id: str, aria_label: str, summary_cards: list[dict[str, Any]]) -> str:
    summary = render_summary_cards(summary_cards)
    escaped_label = html_attr(aria_label)
    return (
        f'{summary}<div class="chart-wrap chart-container" role="img" aria-label="{escaped_label}">'
        f'<canvas id="{html_attr(chart_id)}" aria-label="{escaped_label}"></canvas>'
        f'<p class="sr-only">{html_text(aria_label)}</p></div>'
    )


def render_stat_card(match: re.Match[str]) -> str:
    data = parse_key_value_block(match.group("body"))
    tone = data.get("tone") or "neutral"
    title = f'<div class="stat-card__title">{html_text(data.get("title", ""))}</div>' if data.get("title") else ""
    compare = f'<div class="stat-card__compare">{html_text(data.get("compare", ""))}</div>' if data.get("compare") else ""
    return (
        f'<div class="stat-card stat-card--{html_attr(tone)}">'
        f'<div class="stat-card__label">{html_text(data.get("label", ""))}</div>'
        f'{title}'
        f'<div class="stat-card__value">{html_text(data.get("value", ""))}</div>'
        f'{compare}'
        '</div>'
    )


def compact_date(value: str) -> str:
    return value.replace("-", ".") if value else ""


def period_label(period_start: str, period_end: str) -> str:
    try:
        start = parse_date(period_start, "period_start")
        end = parse_date(period_end, "period_end")
    except SystemExit:
        return f"{period_start}~{period_end}"
    days = (end - start).days + 1
    if 27 <= days <= 32:
        return "최근 30일"
    if 85 <= days <= 95:
        return "최근 3개월"
    if 175 <= days <= 190:
        return "최근 6개월"
    if 360 <= days <= 367:
        return "최근 1년"
    return f"{compact_date(period_start)}~{compact_date(period_end)}"


def format_signed_value(value: Any, currency: str = "") -> str:
    number = normalize_number(value)
    if number is None:
        return "-"
    sign = "+" if float(number) >= 0 else "-"
    absolute = abs(float(number))
    symbol = currency_symbol(currency)
    rendered = f"{int(absolute):,}" if absolute.is_integer() else f"{absolute:,.2f}"
    return f"{sign}{symbol}{rendered}"


def load_primary_price_payload(slug: str) -> dict[str, Any] | None:
    path = ASSET_DIR / f"{slug}-price-chart-v1.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def hero_price_summary(slug: str) -> dict[str, str]:
    payload = load_primary_price_payload(slug)
    if not payload:
        return {"price": "-", "change_pct": "-", "delta": "-", "tone": "neutral"}
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict) and row.get("value") is not None]
    currency = str(payload.get("currency") or "")
    if not rows:
        return {"price": "-", "change_pct": "-", "delta": "-", "tone": "neutral"}
    start_value = rows[0]["value"]
    end_value = rows[-1]["value"]
    try:
        delta = float(end_value) - float(start_value)
        change_pct = ((float(end_value) / float(start_value)) - 1.0) * 100
    except Exception:
        delta = None
        change_pct = None
    tone = "up" if (change_pct or 0) >= 0 else "down"
    arrow = "▲" if tone == "up" else "▼"
    change_label = f"{arrow} {change_pct:+.1f}%" if change_pct is not None else "-"
    return {
        "price": format_value(end_value, currency),
        "change_pct": change_label,
        "delta": format_signed_value(delta, currency) if delta is not None else "-",
        "tone": tone,
    }


def display_name_from_title(title: str, ticker: str) -> str:
    title = (title or "").strip()
    if title:
        cleaned = re.sub(r"\s*(최근|분석|동향|리포트).*$", "", title).strip()
        if cleaned:
            return cleaned.split()[0]
    return ticker or "종목"


def ticker_meta(ticker: str) -> str:
    ticker = ticker or ""
    if ticker.endswith(".KS"):
        return f"{ticker[:-3]} · 코스피"
    if ticker.endswith(".KQ"):
        return f"{ticker[:-3]} · 코스닥"
    return f"{ticker} · 글로벌" if ticker else "시장 리포트"


def logo_text_for(name: str, ticker: str) -> str:
    compact = re.sub(r"\s+", "", name or "")
    if re.search(r"[가-힣]", compact):
        return compact[:2]
    letters = re.findall(r"[A-Za-z]", compact)
    if letters:
        return "".join(letters[:2]).upper()
    return (ticker or "ST")[:2].upper()


def logo_gradient(ticker: str) -> tuple[str, str]:
    ticker_upper = (ticker or "").upper()
    if ticker_upper.startswith("005930"):
        return "#3182F6", "#0B5CD7"
    if ticker_upper.startswith("000660"):
        return "#FF4040", "#C50019"
    if ticker_upper.startswith("TSLA"):
        return "#F04452", "#B91C1C"
    if ticker_upper.startswith("NVDA"):
        return "#76B900", "#2E7D32"
    return "#3182F6", "#1B64DA"


def extract_topic_tags(title: str, subtitle: str, body_html: str, ticker: str, period: str) -> list[tuple[str, bool]]:
    body_text = re.sub(r"<[^>]+>", " ", body_html)
    body_text = re.sub(r"https?://\S+", " ", body_text)
    haystack = f"{title}\n{subtitle}\n{body_text}"
    candidates = [
        "AI", "HBM", "반도체", "메모리", "실적", "수급", "뉴스", "리스크",
        "전기차", "로보택시", "정책", "규제", "환율", "노사", "성과급", "데이터센터",
    ]
    tags: list[tuple[str, bool]] = []
    if ticker:
        tags.append((ticker, True))
    if period:
        tags.append((period, True))
    for term in candidates:
        if term in haystack and all(existing != term for existing, _ in tags):
            tags.append((term, len(tags) < 4))
        if len(tags) >= 6:
            break
    return tags[:6]


def section_subtitle(title_text: str) -> str:
    return {
        "개요": "이번 리포트의 핵심 숫자와 흐름을 먼저 살펴볼게요.",
        "배경": "가격 뒤에 있던 업황과 사건을 차분히 정리했어요.",
        "메커니즘": "무엇이 가격과 심리에 영향을 줬는지 구조로 풀어봤어요.",
        "최신 뉴스 5건 요약": "가장 최근 뉴스에서 반복된 신호를 짧게 모았어요.",
        "영향과 적용": "이 흐름을 해석할 때 어디까지 참고할 수 있는지 정리했어요.",
        "핵심 정리": "마지막으로 기억할 포인트만 다시 모았어요.",
        "References": "검증에 사용한 출처를 한곳에 모았어요.",
    }.get(title_text, "읽기 쉽게 핵심만 나눠서 정리했어요.")


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
        title_text = re.sub(r"<[^>]+>", "", html.unescape(title_html))
        section_id = slugify_heading(title_html)
        toc.append((section_id, title_text))
        divider = "" if index == 0 and not leading else '<hr class="divider">'
        section_body = rendered_html[start:end].strip()
        parts.append(
            f'{divider}<section id="{html_attr(section_id)}">'
            f'<h2>{title_html}</h2><p class="section-sub">{html_text(section_subtitle(title_text))}</p>{section_body}</section>'
        )
    return "\n".join(parts), toc


def css() -> str:
    return """
:root { --toss-blue:#3182F6; --toss-blue-hover:#1B64DA; --toss-blue-bg:#E8F3FF; --toss-blue-bg-soft:#F4F8FF; --gray-900:#191F28; --gray-800:#333D4B; --gray-700:#4E5968; --gray-600:#6B7684; --gray-500:#8B95A1; --gray-400:#B0B8C1; --gray-300:#D1D6DB; --gray-200:#E5E8EB; --gray-100:#F2F4F6; --gray-50:#F9FAFB; --up:#F04452; --up-bg:#FFF0F1; --down:#3182F6; --down-bg:#E8F3FF; --bg:#F9FAFB; --card:#FFFFFF; --text-strong:var(--gray-900); --text-base:var(--gray-700); --text-muted:var(--gray-500); --border:var(--gray-100); }
* { box-sizing:border-box; -webkit-tap-highlight-color:transparent; } html, body { margin:0; padding:0; }
body { background:var(--bg); color:var(--text-base); font-family:"Pretendard Variable", "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, sans-serif; font-size:15px; line-height:1.6; -webkit-font-smoothing:antialiased; letter-spacing:-0.01em; font-variant-numeric:tabular-nums; }
a { color:var(--toss-blue); text-decoration:none; overflow-wrap:anywhere; word-break:break-word; } a:hover { text-decoration:underline; }
main.shell { max-width:560px; margin:0 auto; background:var(--card); min-height:100vh; }
.appbar { position:sticky; top:0; z-index:10; background:rgba(255,255,255,0.95); backdrop-filter:saturate(180%) blur(12px); -webkit-backdrop-filter:saturate(180%) blur(12px); border-bottom:1px solid var(--border); padding:14px 20px; display:flex; align-items:center; gap:12px; }
.appbar__back { width:28px; height:28px; display:flex; align-items:center; justify-content:center; color:var(--gray-900); font-size:22px; line-height:1; } .appbar__title { font-size:16px; font-weight:700; color:var(--gray-900); }
.hero { padding:24px 20px 28px; } .ticker-row { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
.ticker-logo { width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg, var(--logo-from,#3182F6) 0%, var(--logo-to,#1B64DA) 100%); color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:800; letter-spacing:-0.04em; flex-shrink:0; }
.ticker-meta { display:flex; flex-direction:column; gap:2px; min-width:0; } .ticker-name { font-size:17px; font-weight:700; color:var(--gray-900); overflow-wrap:anywhere; } .ticker-code { font-size:12px; color:var(--text-muted); }
.price-block { margin-top:18px; } .price-now { font-size:34px; font-weight:800; color:var(--gray-900); letter-spacing:-0.035em; font-variant-numeric:tabular-nums; line-height:1.15; }
.price-change { margin-top:6px; display:inline-flex; align-items:center; gap:6px; flex-wrap:wrap; font-size:14px; font-weight:700; color:var(--up); font-variant-numeric:tabular-nums; } .price-change--down { color:var(--down); }
.price-change__pill { background:var(--up-bg); color:var(--up); padding:2px 8px; border-radius:999px; font-size:12px; font-weight:700; } .price-change--down .price-change__pill { background:var(--down-bg); color:var(--down); } .price-period { color:var(--text-muted); font-weight:500; font-size:13px; }
.subtitle-line { margin:16px 0 0; font-size:14px; color:var(--text-base); line-height:1.55; } .tag-row { display:flex; gap:6px; flex-wrap:wrap; margin-top:16px; }
.tag { background:var(--gray-100); color:var(--gray-700); padding:6px 12px; border-radius:999px; font-size:12px; font-weight:600; } .tag--blue { background:var(--toss-blue-bg); color:var(--toss-blue); }
.hero-image { margin:18px 0 0; border-radius:16px; overflow:hidden; background:var(--gray-50); border:1px solid var(--border); } .hero-image img { display:block; width:100%; height:auto; aspect-ratio:16/9; object-fit:cover; }
.divider { height:8px; background:var(--gray-50); border:0; margin:0; } .lead-content { padding:24px 20px 8px; color:var(--text-base); font-size:14.5px; }
section { padding:28px 20px 8px; } section h2 { font-size:20px; font-weight:800; color:var(--gray-900); margin:0 0 4px; letter-spacing:-0.025em; } section .section-sub { font-size:13px; color:var(--text-muted); margin:0 0 18px; }
section h3 { font-size:15px; font-weight:700; color:var(--gray-900); margin:24px 0 8px; letter-spacing:-0.02em; } section p { margin:8px 0 14px; color:var(--text-base); font-size:14.5px; line-height:1.7; } section p strong, section li strong { color:var(--gray-900); font-weight:700; } section ul, section ol { padding-left:20px; margin:8px 0 16px; } section li { margin:6px 0; color:var(--text-base); font-size:14.5px; line-height:1.65; overflow-wrap:anywhere; }
blockquote { margin:18px 0; padding:16px 18px; background:var(--toss-blue-bg-soft); border-radius:14px; color:var(--gray-800); font-size:14px; line-height:1.65; border-left:3px solid var(--toss-blue); }
.stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:20px 0 4px; } .stat-card { background:var(--gray-50); border-radius:14px; padding:16px; min-width:0; } .stat-card__label, .stat-card__compare { font-size:12px; color:var(--text-muted); font-weight:500; margin-bottom:6px; } .stat-card__title { font-size:13px; color:var(--gray-700); font-weight:700; margin-bottom:4px; } .stat-card__value { font-size:18px; font-weight:800; color:var(--gray-900); font-variant-numeric:tabular-nums; letter-spacing:-0.02em; overflow-wrap:anywhere; } .stat-card--highlight { background:var(--toss-blue-bg); } .stat-card--highlight .stat-card__value { color:var(--toss-blue); } .stat-card--up .stat-card__value, .chart-summary-card--up .chart-summary-card__value { color:var(--up); } .stat-card--down .stat-card__value, .chart-summary-card--down .chart-summary-card__value { color:var(--down); }
.chart-summary { margin:20px 0 12px; } .chart-wrap { margin:14px 0 8px; padding:4px 0 0; background:var(--card); border-radius:16px; } .chart-wrap canvas { width:100% !important; height:240px !important; } .chart-container { min-height:248px; }
table { width:100%; border-collapse:collapse; display:block; overflow-x:auto; margin:14px 0; } th, td { border-bottom:1px solid var(--border); padding:12px 0; text-align:left; font-size:13.5px; } th { color:var(--text-muted); font-weight:500; } td { color:var(--gray-900); font-weight:600; }
.word-cloud { display:flex; flex-wrap:wrap; gap:8px 14px; align-items:center; padding:16px; background:var(--gray-50); border-radius:14px; } .word-cloud__term { color:var(--gray-900); line-height:1.1; }
#latest-news-5 li, #references li { list-style:none; margin:0; padding:14px 0; border-bottom:1px solid var(--border); } #latest-news-5 ul, #references ul { padding-left:0; margin:12px 0 4px; } #latest-news-5 li:last-child, #references li:last-child { border-bottom:0; } #references li { background:var(--gray-50); border-bottom:0; border-radius:10px; padding:12px 14px; margin-bottom:10px; font-size:13px; }
footer { margin-top:24px; padding:24px 20px 48px; background:var(--gray-50); color:var(--text-muted); font-size:12px; line-height:1.6; } footer p { margin:0 0 6px; }
.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; }
@media (max-width:380px) { .price-now { font-size:30px; } .stat-card__value { font-size:16px; } section h2 { font-size:18px; } }
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
    period = period_label(period_start, period_end)
    company_name = display_name_from_title(title, ticker)
    logo_text = logo_text_for(company_name, ticker)
    logo_from, logo_to = logo_gradient(ticker)
    hero = hero_price_summary(slug)
    change_class = "price-change price-change--down" if hero.get("tone") == "down" else "price-change"
    hero_src = f"assets/{selected_image.name}"
    tags = extract_topic_tags(title, subtitle, body_html, ticker, period)
    tag_html = "".join(f'<span class="tag{" tag--blue" if is_blue else ""}">{html_text(label)}</span>' for label, is_blue in tags)
    scripts = "\n".join(
        f'createTossChart({json.dumps(chart_id)}, {json.dumps(config, ensure_ascii=False)});'
        for chart_id, config in chart_scripts
    )
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="stock-report-harness toss-style-builder">
<meta name="report-slug" content="{html_attr(slug)}">
<meta name="generated-at" content="{html_attr(generated_at)}">
<title>{html_text(title)}</title>
<meta property="og:title" content="{html_attr(title)}">
<meta property="og:description" content="{html_attr(subtitle)}">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>{css()}</style>
</head>
<body>
<main class="shell">
  <div class="appbar" role="banner"><div class="appbar__back" aria-hidden="true">‹</div><div class="appbar__title">종목 리포트</div></div>
  <header class="hero">
    <h1 class="sr-only">{html_text(title)}</h1>
    <div class="ticker-row"><div class="ticker-logo" style="--logo-from:{html_attr(logo_from)};--logo-to:{html_attr(logo_to)}" aria-hidden="true">{html_text(logo_text)}</div><div class="ticker-meta"><div class="ticker-name">{html_text(company_name)}</div><div class="ticker-code">{html_text(ticker_meta(ticker))}</div></div></div>
    <div class="price-block"><div class="price-now">{html_text(hero.get("price", "-"))}</div><div class="{html_attr(change_class)}"><span class="price-change__pill">{html_text(hero.get("change_pct", "-"))}</span><span>{html_text(hero.get("delta", "-"))}</span><span class="price-period">· {html_text(period)}</span></div></div>
    {f'<p class="subtitle-line">{html_text(subtitle)}</p>' if subtitle else ''}
    {f'<div class="tag-row">{tag_html}</div>' if tag_html else ''}
    <figure class="hero-image"><img src="{html_attr(hero_src)}" alt="{html_attr(title)} hero image" loading="eager"></figure>
  </header>
  {body_html}
  <footer id="disclaimer" aria-label="투자 유의사항"><p>{html_text(DEFAULT_DISCLAIMER)}</p><p>작성일 {html_text(created_at or generated_at[:10])} · 분석 기간 {html_text(period_start)} ~ {html_text(period_end)}</p><p>Price data: yfinance ({html_text(ticker)}, daily)</p></footer>
</main>
<script>
Chart.defaults.font.family = 'Pretendard Variable, Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif';
function tossFormatNumber(value, currency) {{ const n = Number(value); if (!Number.isFinite(n)) return String(value ?? ''); const p = currency === 'USD' ? '$' : currency === 'KRW' ? '₩' : currency === 'JPY' ? '¥' : currency === 'EUR' ? '€' : ''; return p + n.toLocaleString(undefined, {{ maximumFractionDigits: n % 1 === 0 ? 0 : 2 }}); }}
function createTossChart(chartId, config) {{
  const canvas = document.getElementById(chartId); if (!canvas) return; const ctx = canvas.getContext('2d'); const cfg = config || {{}}; const currency = cfg.currency || ''; delete cfg.currency;
  const gradient = ctx.createLinearGradient(0, 0, 0, 240); gradient.addColorStop(0, 'rgba(49, 130, 246, 0.22)'); gradient.addColorStop(1, 'rgba(49, 130, 246, 0.0)');
  cfg.data = cfg.data || {{}}; cfg.data.datasets = (cfg.data.datasets || []).map((d) => ({{ ...d, borderColor:'#3182F6', backgroundColor:gradient, borderWidth:2.2, pointRadius:0, pointHitRadius:6, pointHoverRadius:5, pointHoverBackgroundColor:'#3182F6', pointHoverBorderColor:'#FFFFFF', pointHoverBorderWidth:2, fill:true, tension:0.28 }}));
  const oldOptions = cfg.options || {{}}; const oldPlugins = oldOptions.plugins || {{}}; const oldScales = oldOptions.scales || {{}};
  cfg.options = {{ ...oldOptions, responsive:true, maintainAspectRatio:false, interaction:{{ mode:'index', intersect:false }}, plugins:{{ ...oldPlugins, legend:{{ display:false }}, tooltip:{{ backgroundColor:'#191F28', titleColor:'#B0B8C1', bodyColor:'#FFFFFF', padding:10, cornerRadius:8, titleFont:{{ size:11, weight:'normal' }}, bodyFont:{{ size:13, weight:'bold' }}, displayColors:false, callbacks:{{ label:function(c) {{ return tossFormatNumber(c.parsed.y, currency); }} }} }} }}, scales:{{ ...oldScales, x:{{ ticks:{{ maxTicksLimit:6, font:{{ size:10, family:'Pretendard' }}, color:'#8B95A1' }}, grid:{{ display:false }}, border:{{ display:false }} }}, y:{{ position:'right', ticks:{{ callback:function(v) {{ const n = Number(v); if (currency === 'KRW' && Math.abs(n) >= 10000) return (n / 10000).toFixed(0) + '만'; return tossFormatNumber(n, currency); }}, font:{{ size:10, family:'Pretendard' }}, color:'#8B95A1', padding:4 }}, grid:{{ color:'#F2F4F6', drawTicks:false }}, border:{{ display:false }} }} }} }};
  new Chart(ctx, cfg);
}}
{scripts}
</script>
</body>
</html>
"""

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
