#!/usr/bin/env python3
"""Validate the project memory schema.

This script is intentionally dependency-free so hooks and release checks can run it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"
DAILY = MEMORY / "_daily"
TOPICS = MEMORY / "topics"

DAILY_TITLE = re.compile(r"^# (\d{4}-\d{2}-\d{2})\s*$")
DAILY_ENTRY = re.compile(r"^## Entry: (\d{4}-\d{2}-\d{2}) — .+\s*$", re.MULTILINE)
TOPIC_ENTRY = re.compile(r"^## ENTRY-(\d{3}): .+\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^\*\*(상황|증상|원인|해결|검증|일자)\*\*\s*$", re.MULTILINE)
REQUIRED_DAILY = ["상황", "증상", "원인", "해결", "검증"]
REQUIRED_TOPIC = ["상황", "증상", "원인", "해결", "검증", "일자"]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{rel(path)}: {message}")


def validate_daily(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        fail(errors, path, "빈 파일임")
        return

    title = DAILY_TITLE.match(lines[0])
    if not title:
        fail(errors, path, "첫 줄은 '# YYYY-MM-DD' 이어야 함")
    elif path.stem != title.group(1):
        fail(errors, path, "파일명 날짜와 첫 줄 날짜가 다름")

    entries = list(DAILY_ENTRY.finditer(text))
    if not entries and len([line for line in lines[1:] if line.strip()]) > 0:
        fail(errors, path, "본문이 있지만 '## Entry: YYYY-MM-DD — 제목' entry가 없음")

    for idx, match in enumerate(entries):
        start = match.end()
        end = entries[idx + 1].start() if idx + 1 < len(entries) else len(text)
        block = text[start:end]
        entry_date = match.group(1)
        if title and entry_date != title.group(1):
            fail(errors, path, f"entry 날짜 {entry_date}가 daily 날짜와 다름")
        for section in REQUIRED_DAILY:
            if not re.search(rf"^- \*\*{section}\*\*: .+", block, re.MULTILINE):
                fail(errors, path, f"daily entry에 '- **{section}**:' 항목이 없거나 비어 있음")


def validate_topic(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 200:
        fail(errors, path, "200라인 초과함. {slug}-2.md로 분할해야 함")

    bad_headers = [line for line in lines if line.startswith("#") and not line.startswith("## ENTRY-")]
    if bad_headers:
        fail(errors, path, "topic에는 '## ENTRY-001:' 외 markdown header를 추가하면 안 됨")

    entries = list(TOPIC_ENTRY.finditer(text))
    if not entries and text.strip():
        fail(errors, path, "topic 본문이 있지만 '## ENTRY-001: 제목' entry가 없음")
        return

    for idx, match in enumerate(entries):
        start = match.end()
        end = entries[idx + 1].start() if idx + 1 < len(entries) else len(text)
        block = text[start:end]
        sections = SECTION_RE.findall(block)
        if sections != REQUIRED_TOPIC:
            fail(
                errors,
                path,
                f"ENTRY-{match.group(1)} 섹션 순서/개수가 틀림: {sections!r}",
            )
        for section in REQUIRED_TOPIC:
            section_match = re.search(
                rf"^\*\*{section}\*\*\s*\n(?P<body>.*?)(?=^\*\*|\Z)",
                block,
                re.MULTILINE | re.DOTALL,
            )
            if not section_match or not section_match.group("body").strip():
                fail(errors, path, f"ENTRY-{match.group(1)}의 **{section}** 본문이 비어 있음")


def main() -> int:
    errors: list[str] = []
    if not MEMORY.is_dir():
        errors.append("memory/: 디렉터리가 없음")
    if not DAILY.is_dir():
        errors.append("memory/_daily/: 디렉터리가 없음")
    if not TOPICS.is_dir():
        errors.append("memory/topics/: 디렉터리가 없음")

    for path in sorted(DAILY.glob("*.md")) if DAILY.is_dir() else []:
        validate_daily(path, errors)

    for path in sorted(TOPICS.glob("*.md")) if TOPICS.is_dir() else []:
        validate_topic(path, errors)

    if errors:
        print("Memory schema validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Memory schema validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
