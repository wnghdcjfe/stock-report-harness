#!/usr/bin/env python3
"""Inject relevant memory topics for prompt-time context.

Claude Code UserPromptSubmit hook compatible output:
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "..."
  }
}

The script is also safe to run manually:
  echo '{"prompt":"/stock-build foo"}' | python3 scripts/memory_context.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"
TOPICS = MEMORY / "topics"
MAX_TOPIC_CHARS = 6000
MAX_TOTAL_CHARS = 18000

DOMAIN_RULES: list[dict[str, Any]] = [
    {
        "name": "날짜/기간/yfinance 시간 동기화",
        "file": "time-sync.md",
        "patterns": [
            r"\b(period_start|period_end|created_at|interval=1d|yfinance|price-chart)\b",
            r"최근\s*\d+\s*(일|개월|년)",
            r"기간|날짜|거래일|일봉|차트|주가|가격",
        ],
    },
    {
        "name": "외부 API 호출",
        "file": "external-api.md",
        "patterns": [
            r"\b(OpenAI|ElevenLabs|API|image_gen|imagegen|yfinance|requests|fetch|curl)\b",
            r"뉴스|토스증권|Google News|외부\s*호출|API\s*호출",
        ],
    },
    {
        "name": "hero 이미지 워크플로",
        "file": "image-workflow.md",
        "patterns": [
            r"\b(hero|selected-image|image-manifest|image_gen|imagegen)\b",
            r"이미지|프롬프트|후보\s*3|선택된\s*이미지|비주얼",
        ],
    },
    {
        "name": "경제리포트 파이프라인 순서",
        "file": "pipeline-order.md",
        "patterns": [
            r"/(?:stock-plan|stock-research|stock-draft|stock-image|stock-review|stock-build)\b",
            r"\b(plan|research|drafts|reviews|output)/",
            r"빌드|리서치|드래프트|리뷰|경제리포트|HTML|파이프라인",
        ],
    },
    {
        "name": "빌드/설치 오류",
        "file": "build-errors.md",
        "patterns": [
            r"\b(uv sync|pnpm install|npm install|pip install|node|python|build|lint|typecheck|pytest)\b",
            r"빌드|설치|의존성|패키지|테스트|검증",
        ],
    },
    {
        "name": "git workflow",
        "file": "git-workflow.md",
        "patterns": [
            r"\b(git|commit|push|pull request|PR|branch|merge|rebase)\b",
            r"커밋|푸시|브랜치|병합",
        ],
    },
    {
        "name": "guardrails/hook/schema",
        "file": "guardrails.md",
        "patterns": [
            r"\b(hook|validator|schema|AGENTS\.md|CLAUDE\.md|settings\.json)\b",
            r"가드레일|검증기|스키마|차단|훅|메모리|memory",
        ],
    },
]


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {"prompt": raw}


def extract_prompt(data: dict[str, Any]) -> str:
    candidates = [
        data.get("prompt"),
        data.get("message"),
        data.get("user_prompt"),
        data.get("input"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return json.dumps(data, ensure_ascii=False)


def match_rules(prompt: str) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for rule in DOMAIN_RULES:
        if any(re.search(pattern, prompt, re.IGNORECASE) for pattern in rule["patterns"]):
            matched.append(rule)
    return matched


def compact_topic(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return ""
    if len(text) <= MAX_TOPIC_CHARS:
        return text
    return text[:MAX_TOPIC_CHARS].rstrip() + "\n\n... (topic이 길어 앞부분만 자동 주입함)"


def build_context(prompt: str) -> str:
    matched = match_rules(prompt)
    loaded: list[tuple[str, str, str]] = []
    missing: list[tuple[str, str]] = []

    for rule in matched:
        path = TOPICS / rule["file"]
        if path.is_file():
            content = compact_topic(path)
            if content:
                loaded.append((rule["name"], f"memory/topics/{rule['file']}", content))
            else:
                missing.append((rule["name"], f"memory/topics/{rule['file']} (빈 파일)"))
        else:
            missing.append((rule["name"], f"memory/topics/{rule['file']} (없음)"))

    if not loaded and not matched:
        return (
            "[Memory System]\n"
            "관련 memory topic 자동 매칭 없음. 실패/고비용 재시도 관측이 생기면 "
            "memory/_daily/YYYY-MM-DD.md에 1 entry = 1 관측으로 기록함."
        )

    lines: list[str] = [
        "[Memory System 자동 주입]",
        "작업 전 아래 topic 관측을 우선 적용함. 무관한 topic은 로드하지 않았음.",
    ]

    total = sum(len(line) + 1 for line in lines)
    for name, relpath, content in loaded:
        block = f"\n--- {name}: {relpath} ---\n{content}\n"
        if total + len(block) > MAX_TOTAL_CHARS:
            lines.append("\n... (memory 자동 주입 총량 제한으로 일부 topic 생략함)")
            break
        lines.append(block)
        total += len(block)

    if missing:
        lines.append("\n[Memory topic 상태]")
        for name, relpath in missing:
            lines.append(f"- {name}: {relpath}")

    lines.append(
        "\n[기록 규칙] 실패/재시도 비용이 큰 관측은 memory/_daily/YYYY-MM-DD.md에 append하고, "
        "반복/고비용 패턴은 memory/topics/{slug}.md로 추출함."
    )
    return "\n".join(lines)


def main() -> int:
    data = read_stdin_json()
    prompt = extract_prompt(data)
    context = build_context(prompt)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
