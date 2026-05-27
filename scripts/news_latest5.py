#!/usr/bin/env python3
"""Extract the five newest news items from a latest100 JSON artifact.

The report agents use this as a deterministic helper before drafting/building
HTML news sections. It supports the repository's Toss and Google News artifacts
and degrades honestly when a provider does not expose per-item article URLs.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

URL_KEYS = (
    "url",
    "link",
    "article_url",
    "articleUrl",
    "original_url",
    "originalUrl",
    "canonical_url",
    "canonicalUrl",
    "google_news_link",
    "news_url",
    "newsUrl",
)
DATE_KEYS = (
    "published_at_utc",
    "publishedAt",
    "createdAt",
    "updatedAt",
    "date",
)


def flatten_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("body", "items", "articles", "news", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = flatten_items(value)
            if nested:
                return nested
    return []


def parse_dt(value: Any) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return datetime.min.replace(tzinfo=timezone.utc)


def item_datetime(item: dict[str, Any]) -> datetime:
    values = [parse_dt(item.get(key)) for key in DATE_KEYS]
    return max(values)


def source_name(item: dict[str, Any]) -> str:
    source = item.get("source")
    if isinstance(source, dict):
        return str(source.get("name") or source.get("title") or source.get("code") or "").strip()
    return str(source or item.get("publisher") or item.get("provider") or "").strip()


def find_url(item: dict[str, Any], fallback_stock_news_url: str | None = None) -> tuple[str, bool]:
    for key in URL_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value, False
    if fallback_stock_news_url:
        return fallback_stock_news_url, True
    title = str(item.get("title") or "").strip()
    src = source_name(item)
    if title:
        return f"https://www.google.com/search?q={quote_plus(title + ' ' + src)}", True
    return "", True


def summarize(item: dict[str, Any], max_chars: int = 150) -> str:
    title = str(item.get("title") or "").strip()
    raw = str(item.get("summary") or item.get("contentText") or item.get("description") or title).strip()
    raw = re.sub(r"\s+", " ", raw)
    if title and raw.startswith(title):
        raw = raw[len(title) :].strip(" -—:|\n") or title
    # Keep the first compact sentence/phrase, not a full article excerpt.
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", raw)
    summary = next((part.strip() for part in parts if part.strip()), raw)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary


def infer_market_interpretation(item: dict[str, Any]) -> str:
    explicit = item.get("market_interpretation") or item.get("price_supply_interpretation") or item.get("impact")
    if explicit:
        return str(explicit).strip()
    category = str(item.get("category") or item.get("issue") or "").strip()
    mapping = {
        "노사": "노사·보상 비용 이슈로 단기 리스크 프리미엄과 비용 부담을 함께 점검할 뉴스다.",
        "성과급": "성과급·임금 비용이 수익성 기대와 투자심리에 영향을 줄 수 있다.",
        "임금": "임금 비용과 내부 봉합 여부가 단기 심리 변수다.",
        "시장": "동종 업종·지수 흐름과 함께 수급 심리를 확인할 뉴스다.",
        "반도체": "반도체 업황 기대와 대형주 수급에 연결되는 뉴스다.",
        "AI": "AI/HBM 수요 기대와 제품 믹스 개선 기대에 연결되는 뉴스다.",
        "환율": "환율·외국인 자금 흐름이 단기 변동성 요인으로 작동할 수 있다.",
        "외국인": "외국인 수급 방향과 지수 레벨을 함께 확인할 뉴스다.",
        "정책": "정책·지역 투자 기대가 중장기 수급 서사에 영향을 줄 수 있다.",
        "거래": "정규장 가격 흐름과 분리해 확인해야 할 거래 데이터 노이즈일 수 있다.",
    }
    for key, interpretation in mapping.items():
        if key in category:
            return interpretation
    return "가격·수급 영향은 직접 단정하지 말고 같은 날 주가·거래량·외국인/기관 수급과 함께 확인해야 한다."


def normalize(item: dict[str, Any], fallback_stock_news_url: str | None) -> dict[str, Any]:
    dt = item_datetime(item)
    url, fallback = find_url(item, fallback_stock_news_url)
    return {
        "date": dt.isoformat() if dt.year > 1 else "",
        "source": source_name(item),
        "title": str(item.get("title") or "").strip(),
        "category": str(item.get("category") or item.get("issue") or "").strip(),
        "summary": summarize(item),
        "market_interpretation": infer_market_interpretation(item),
        "url": url,
        "url_is_fallback": fallback,
    }


def render_markdown(items: list[dict[str, Any]]) -> str:
    lines = ["### 최신 뉴스 5건 요약", ""]
    for idx, item in enumerate(items, 1):
        date = item["date"][:16].replace("T", " ") if item["date"] else "날짜 미상"
        title = item["title"] or "제목 없음"
        source = item["source"] or "출처 미상"
        safe_title = title.replace("[", "\\[").replace("]", "\\]")
        label = f"[{safe_title}]({item['url']})" if item["url"] else safe_title
        fallback_note = " _(원문 URL 미제공: 제공사 뉴스 목록/검색으로 연결)_" if item["url_is_fallback"] else ""
        category = f" / {item['category']}" if item["category"] else ""
        lines.append(f"{idx}. **{date} · {source}{category}** — {label}{fallback_note}")
        lines.append(f"   - 요약: {item['summary']}")
        lines.append(f"   - 가격/수급 해석: {item['market_interpretation']}")
    return "\n".join(lines) + "\n"


def render_html(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        date = item["date"][:16].replace("T", " ") if item["date"] else "날짜 미상"
        title = html.escape(item["title"] or "제목 없음")
        source = html.escape(item["source"] or "출처 미상")
        category = html.escape(item["category"] or "")
        summary = html.escape(item["summary"])
        market_interpretation = html.escape(item["market_interpretation"])
        href = html.escape(item["url"], quote=True)
        note = "<span class=\"news-link-note\">원문 URL 미제공: 제공사 뉴스 목록/검색으로 연결</span>" if item["url_is_fallback"] else ""
        link = f'<a href="{href}" target="_blank" rel="noopener noreferrer">{title}</a>' if href else title
        rows.append(
            "<li>"
            f"<strong>{date} · {source}</strong>"
            f"{' <em>' + category + '</em>' if category else ''}<br />"
            f"{link} {note}"
            f"<p>{summary}</p>"
            f"<p><strong>가격/수급 해석:</strong> {market_interpretation}</p>"
            "</li>"
        )
    return '<section id="latest-news-5"><h2>최신 뉴스 5건 요약</h2><ol class="latest-news-list">' + "".join(rows) + "</ol></section>\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--format", choices=("markdown", "html", "json"), default="markdown")
    parser.add_argument("--fallback-stock-news-url", help="Provider news-list URL to use only when per-item URL is unavailable.")
    args = parser.parse_args()

    payload = json.loads(args.json_path.read_text(encoding="utf-8"))
    items = flatten_items(payload)
    newest = sorted(items, key=item_datetime, reverse=True)[:5]
    normalized = [normalize(item, args.fallback_stock_news_url) for item in newest]
    if args.format == "json":
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
    elif args.format == "html":
        print(render_html(normalized), end="")
    else:
        print(render_markdown(normalized), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
