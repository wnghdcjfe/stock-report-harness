#!/usr/bin/env python3
"""Shared helpers for stock-report-harness contract validation/building.

The helpers are deliberately small and dependency-light.  PyYAML is used when
available for frontmatter fidelity, but the fallback parser is enough for the
flat scalar keys that the pipeline contracts depend on.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "plan"
RESEARCH_DIR = ROOT / "research"
DRAFT_DIR = ROOT / "drafts"
REVIEW_DIR = ROOT / "reviews"
OUTPUT_DIR = ROOT / "output"
ASSET_DIR = OUTPUT_DIR / "assets"

FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(?P<frontmatter>.*?)\r?\n---\s*(?:\r?\n)?", re.DOTALL)
H1_RE = re.compile(r"^#(?!#)\s+.+$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
PRICE_CHART_FENCE_RE = re.compile(r"```price-chart\s*\n(?P<body>.*?)\n```", re.DOTALL)
SOURCE_MARKER_RE = re.compile(r"\[(?:S|N|P)\d+\]")

REQUIRED_DRAFT_SECTIONS = ["개요", "배경", "메커니즘", "영향과 적용", "References"]


@dataclass(frozen=True)
class ArtifactPaths:
    slug: str
    plan: Path
    research: Path
    draft: Path
    review: Path
    html: Path
    selected_image_json: Path
    price_chart_json: Path


def artifact_paths(slug: str) -> ArtifactPaths:
    return ArtifactPaths(
        slug=slug,
        plan=PLAN_DIR / f"{slug}.md",
        research=RESEARCH_DIR / f"{slug}.md",
        draft=DRAFT_DIR / f"{slug}.md",
        review=REVIEW_DIR / f"{slug}.md",
        html=OUTPUT_DIR / f"{slug}.html",
        selected_image_json=ASSET_DIR / f"{slug}-selected-image.json",
        price_chart_json=ASSET_DIR / f"{slug}-price-chart-v1.json",
    )


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _stringify_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    if isinstance(value, dict):
        return {str(k): _stringify_scalar(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify_scalar(v) for v in value]
    return value


def _fallback_yamlish_parse(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if current_key and line.strip().startswith("- "):
                data.setdefault(current_key, [])
                if isinstance(data[current_key], list):
                    data[current_key].append(line.strip()[2:].strip().strip('"\''))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        elif value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        else:
            data[key] = value.strip('"\'')
    return data


def parse_frontmatter_text(text: str) -> tuple[dict[str, Any], str, str]:
    """Return (frontmatter, body, raw_frontmatter)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, ""

    raw = match.group("frontmatter")
    parsed: Any
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(raw) or {}
        if not isinstance(parsed, dict):
            parsed = {}
    except Exception:
        parsed = _fallback_yamlish_parse(raw)

    parsed = {str(k): _stringify_scalar(v) for k, v in parsed.items()}
    return parsed, text[match.end() :], raw


def read_markdown(path: Path) -> tuple[dict[str, Any], str, str, str]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body, raw = parse_frontmatter_text(text)
    return frontmatter, body, raw, text


def frontmatter_value(frontmatter: dict[str, Any], key: str) -> str:
    value = frontmatter.get(key)
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def heading_titles(body: str) -> list[str]:
    return [m.group("title").strip().rstrip("#").strip() for m in H2_RE.finditer(body)]


def has_required_section(body: str, section: str) -> bool:
    return any(title == section for title in heading_titles(body))


def count_h1(body: str) -> int:
    return len(H1_RE.findall(body))


def price_chart_blocks(body: str) -> list[dict[str, str]]:
    return [parse_key_value_block(match.group("body")) for match in PRICE_CHART_FENCE_RE.finditer(body)]


def has_source_markers(text: str) -> bool:
    return bool(SOURCE_MARKER_RE.search(text))


def strip_source_markers(text: str) -> str:
    # Remove adjacent source markers and the extra whitespace they often leave.
    stripped = SOURCE_MARKER_RE.sub("", text)
    stripped = re.sub(r"\s+([.,;:!?])", r"\1", stripped)
    stripped = re.sub(r" {2,}", " ", stripped)
    return stripped


def parse_key_value_block(raw: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_image_path(slug: str) -> tuple[Path | None, dict[str, Any] | None]:
    selected_json = artifact_paths(slug).selected_image_json
    if not selected_json.is_file():
        return None, None
    payload = load_json(selected_json)
    if not isinstance(payload, dict):
        return None, payload
    value = (
        payload.get("selected_image")
        or payload.get("selectedImage")
        or payload.get("image")
        or payload.get("image_path")
        or payload.get("path")
        or payload.get("file")
    )
    if not isinstance(value, str) or not value.strip():
        return None, payload

    raw = value.strip()
    raw_path = Path(raw)
    candidates: list[Path] = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.extend(
            [
                ROOT / raw_path,
                OUTPUT_DIR / raw_path,
                ASSET_DIR / raw_path,
            ]
        )
        if raw.startswith("assets/"):
            candidates.append(OUTPUT_DIR / raw_path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate, payload
    # Return the most likely path for helpful diagnostics even when missing.
    return candidates[-1] if candidates else None, payload


def html_attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def html_text(value: Any) -> str:
    return html.escape(str(value), quote=False)
