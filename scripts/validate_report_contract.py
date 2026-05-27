#!/usr/bin/env python3
"""Validate stock-report-harness pipeline artifacts for one report slug.

Usage:
  python3 scripts/validate_report_contract.py <slug>
  python3 scripts/validate_report_contract.py <slug> --require-html --require-price-chart
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from report_contract_lib import (
    REQUIRED_DRAFT_SECTIONS,
    ROOT,
    artifact_paths,
    count_h1,
    frontmatter_value,
    has_required_section,
    has_source_markers,
    price_chart_blocks,
    read_markdown,
    rel,
    selected_image_path,
    load_json,
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ValidationResult:
    slug: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check(self, message: str) -> None:
        self.checks.append(message)


def _load_required_markdown(path: Path, result: ValidationResult) -> tuple[dict[str, Any], str] | None:
    if not path.is_file():
        result.error(f"필수 파일 없음: {rel(path)}")
        return None
    frontmatter, body, _, _ = read_markdown(path)
    if not frontmatter:
        result.error(f"frontmatter 없음 또는 파싱 실패: {rel(path)}")
    return frontmatter, body


def _expect_source_path(frontmatter: dict[str, Any], key: str, expected: Path, owner: Path, result: ValidationResult) -> None:
    actual = frontmatter_value(frontmatter, key)
    if not actual:
        result.error(f"{rel(owner)} frontmatter `{key}` 누락")
        return
    if actual != rel(expected):
        result.error(f"{rel(owner)} frontmatter `{key}` 불일치: {actual!r} != {rel(expected)!r}")


def _validate_common_frontmatter(
    slug: str,
    loaded: dict[str, tuple[Path, dict[str, Any], str]],
    result: ValidationResult,
) -> None:
    # plan/research/draft are the canonical ticker/period carriers. Review has
    # status/source-path metadata by contract and may not duplicate ticker/date.
    canonical_keys = ["slug", "ticker", "period_start", "period_end"]
    values: dict[str, dict[str, str]] = {key: {} for key in canonical_keys}

    for name in ("plan", "research", "draft"):
        path, frontmatter, _body = loaded[name]
        for key in canonical_keys:
            value = frontmatter_value(frontmatter, key)
            if not value:
                result.error(f"{rel(path)} frontmatter `{key}` 누락")
                continue
            values[key][name] = value

    review_path, review_fm, _review_body = loaded["review"]
    review_slug = frontmatter_value(review_fm, "slug")
    if not review_slug:
        result.error(f"{rel(review_path)} frontmatter `slug` 누락")
    elif review_slug != slug:
        result.error(f"{rel(review_path)} frontmatter `slug` 불일치: {review_slug!r} != {slug!r}")

    for key, by_file in values.items():
        unique = {value for value in by_file.values() if value}
        if key == "slug" and unique and unique != {slug}:
            result.error(f"frontmatter `slug` 불일치: {by_file!r}; expected {slug!r}")
        elif len(unique) > 1:
            result.error(f"frontmatter `{key}` 불일치: {by_file!r}")

    for date_key in ("period_start", "period_end"):
        for name, value in values[date_key].items():
            if value and not DATE_RE.match(value):
                result.error(f"{name} frontmatter `{date_key}` 형식 오류: {value!r} (YYYY-MM-DD 필요)")

    result.check("plan/research/draft slug·ticker·period frontmatter consistency")


def _validate_draft(slug: str, draft_path: Path, draft_body: str, result: ValidationResult) -> None:
    h1_count = count_h1(draft_body)
    if h1_count != 1:
        result.error(f"{rel(draft_path)} H1 개수 오류: {h1_count}개 (정확히 1개 필요)")
    else:
        result.check("draft H1 exactly one")

    for section in REQUIRED_DRAFT_SECTIONS:
        if not has_required_section(draft_body, section):
            result.error(f"{rel(draft_path)} 필수 섹션 누락: ## {section}")
    result.check("draft required sections present")

    if not price_chart_blocks(draft_body):
        result.error(f"{rel(draft_path)} `price-chart` fenced block 없음")
    else:
        result.check("draft price-chart block present")

    # If a latest100 artifact exists, the draft must carry the 5-news section.
    news_artifacts = list((ROOT / "output" / "assets").glob(f"{slug}-*-latest100.json"))
    if news_artifacts and not has_required_section(draft_body, "최신 뉴스 5건 요약"):
        result.error(
            f"100건 뉴스 원자료가 있으나 draft 필수 섹션 누락: ## 최신 뉴스 5건 요약 "
            f"(artifacts: {', '.join(rel(p) for p in news_artifacts[:3])})"
        )


def _validate_review(paths, review_fm: dict[str, Any], result: ValidationResult) -> None:
    status = frontmatter_value(review_fm, "status")
    if status != "pass":
        result.error(f"{rel(paths.review)} review status가 pass가 아님: {status!r}")
    else:
        result.check("review status pass")
    _expect_source_path(review_fm, "plan_source", paths.plan, paths.review, result)
    _expect_source_path(review_fm, "research_source", paths.research, paths.review, result)
    _expect_source_path(review_fm, "draft_source", paths.draft, paths.review, result)

    if frontmatter_value(review_fm, "review_type") != "separate-session-4way":
        result.error(f"{rel(paths.review)} review_type은 separate-session-4way 여야 함")
    if frontmatter_value(review_fm, "review_execution") != "separate_subagent_sessions":
        result.error(f"{rel(paths.review)} review_execution은 separate_subagent_sessions 여야 함")


def _validate_selected_image(slug: str, result: ValidationResult) -> None:
    paths = artifact_paths(slug)
    if not paths.selected_image_json.is_file():
        result.error(f"selected-image JSON 없음: {rel(paths.selected_image_json)}")
        return
    image_path, payload = selected_image_path(slug)
    if not isinstance(payload, dict):
        result.error(f"selected-image JSON은 object여야 함: {rel(paths.selected_image_json)}")
        return
    if image_path is None:
        result.error(f"selected-image JSON에서 이미지 경로를 찾을 수 없음: {rel(paths.selected_image_json)}")
        return
    if not image_path.is_file():
        result.error(f"selected hero PNG 없음: {rel(image_path)}")
        return
    if image_path.suffix.lower() != ".png":
        result.error(f"selected hero는 PNG여야 함: {rel(image_path)}")
        return
    result.check("selected-image JSON and PNG present")


def _validate_price_chart_json(
    slug: str,
    ticker: str,
    period_start: str,
    period_end: str,
    require_price_chart: bool,
    result: ValidationResult,
) -> None:
    paths = artifact_paths(slug)
    if not paths.price_chart_json.is_file():
        if require_price_chart:
            result.error(f"price chart JSON 없음: {rel(paths.price_chart_json)}")
        else:
            result.warn(f"price chart JSON 아직 없음: {rel(paths.price_chart_json)}")
        return

    try:
        payload = load_json(paths.price_chart_json)
    except Exception as exc:
        result.error(f"price chart JSON 파싱 실패: {rel(paths.price_chart_json)}: {exc}")
        return
    if not isinstance(payload, dict):
        result.error(f"price chart JSON은 object여야 함: {rel(paths.price_chart_json)}")
        return

    expected = {"slug": slug, "ticker": ticker, "period_start": period_start, "period_end": period_end}
    for key, value in expected.items():
        actual = str(payload.get(key) or "")
        if actual != value:
            result.error(f"price chart JSON `{key}` 불일치: {actual!r} != {value!r}")

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        result.error(f"price chart JSON `rows`가 비어 있음: {rel(paths.price_chart_json)}")
    else:
        dates = [str(row.get("date") or "") for row in rows if isinstance(row, dict)]
        if dates != sorted(dates):
            result.error(f"price chart JSON `rows[].date`가 오름차순이 아님: {rel(paths.price_chart_json)}")
        if any(not DATE_RE.match(d) for d in dates):
            result.error(f"price chart JSON `rows[].date`는 YYYY-MM-DD여야 함: {rel(paths.price_chart_json)}")

    chart = payload.get("chart")
    aria_label = payload.get("ariaLabel") or payload.get("aria_label")
    labels: Any = None
    if isinstance(chart, dict):
        data = chart.get("data")
        if isinstance(data, dict):
            labels = data.get("labels")
    if labels is not None:
        if not isinstance(labels, list) or labels != sorted(labels):
            result.error(f"price chart JSON chart.data.labels가 오름차순 배열이 아님: {rel(paths.price_chart_json)}")
    if require_price_chart and not aria_label:
        result.error(f"price chart JSON ariaLabel 누락: {rel(paths.price_chart_json)}")
    result.check("price chart JSON shape and identity")


def _validate_html(slug: str, require_html: bool, result: ValidationResult) -> None:
    paths = artifact_paths(slug)
    if not paths.html.is_file():
        if require_html:
            result.error(f"HTML 없음: {rel(paths.html)}")
        else:
            result.warn(f"HTML 아직 없음: {rel(paths.html)}")
        return
    text = paths.html.read_text(encoding="utf-8")
    if not text.strip():
        result.error(f"HTML이 비어 있음: {rel(paths.html)}")
        return
    if has_source_markers(text):
        result.error(f"최종 HTML에 [S1]/[N1]/[P1]류 source marker 잔존: {rel(paths.html)}")
    disclaimer_terms = ("투자 조언", "투자 권유", "투자 자문", "교육용", "교육 및", "매수", "매도")
    if not any(term in text for term in disclaimer_terms):
        result.error(f"최종 HTML footer 투자 유의 문구를 찾을 수 없음: {rel(paths.html)}")
    image_path, _ = selected_image_path(slug)
    if image_path and image_path.is_file():
        image_name = image_path.name
        if image_name not in text:
            result.error(f"최종 HTML에 selected hero 이미지 참조 없음: {image_name}")
    result.check("HTML exists, marker-free, and references selected image")


def validate_contract(
    slug: str,
    *,
    require_html: bool = False,
    require_price_chart: bool = False,
    check_html_if_present: bool = True,
    check_price_chart_if_present: bool = True,
) -> ValidationResult:
    result = ValidationResult(slug=slug)
    paths = artifact_paths(slug)
    required = {
        "plan": paths.plan,
        "research": paths.research,
        "draft": paths.draft,
        "review": paths.review,
    }

    loaded: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for name, path in required.items():
        data = _load_required_markdown(path, result)
        if data is None:
            continue
        frontmatter, body = data
        loaded[name] = (path, frontmatter, body)

    if len(loaded) == len(required):
        _validate_common_frontmatter(slug, loaded, result)
        plan_path, _plan_fm, _plan_body = loaded["plan"]
        research_path, research_fm, _research_body = loaded["research"]
        draft_path, draft_fm, draft_body = loaded["draft"]
        _review_path, review_fm, _review_body = loaded["review"]

        _expect_source_path(research_fm, "plan_source", paths.plan, research_path, result)
        _expect_source_path(draft_fm, "plan_source", paths.plan, draft_path, result)
        _expect_source_path(draft_fm, "research_source", paths.research, draft_path, result)
        _validate_draft(slug, draft_path, draft_body, result)
        _validate_review(paths, review_fm, result)
        _validate_selected_image(slug, result)
        if require_price_chart or check_price_chart_if_present:
            _validate_price_chart_json(
                slug,
                frontmatter_value(draft_fm, "ticker") or frontmatter_value(loaded["plan"][1], "ticker"),
                frontmatter_value(draft_fm, "period_start") or frontmatter_value(loaded["plan"][1], "period_start"),
                frontmatter_value(draft_fm, "period_end") or frontmatter_value(loaded["plan"][1], "period_end"),
                require_price_chart,
                result,
            )
        if require_html or check_html_if_present:
            _validate_html(slug, require_html, result)

    return result


def print_result(result: ValidationResult) -> None:
    title = "PASS" if result.ok else "FAIL"
    print(f"[{title}] report contract: {result.slug}")
    for check in result.checks:
        print(f"  ok - {check}")
    for warning in result.warnings:
        print(f"  warn - {warning}")
    for error in result.errors:
        print(f"  error - {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Report slug, e.g. samsung-electronics-recent-30d-2026-05")
    parser.add_argument("--require-html", action="store_true", help="Fail when output/<slug>.html is missing")
    parser.add_argument(
        "--require-price-chart",
        action="store_true",
        help="Fail when output/assets/<slug>-price-chart-v1.json is missing or lacks ariaLabel",
    )
    args = parser.parse_args(argv)

    result = validate_contract(args.slug, require_html=args.require_html, require_price_chart=args.require_price_chart)
    print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
