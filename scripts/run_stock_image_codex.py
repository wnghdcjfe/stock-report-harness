#!/usr/bin/env python3
"""Run the stock-image stage through Codex CLI + the Codex imagegen skill.

This wrapper keeps the stock-report-harness file contract deterministic while
outsourcing the actual raster generation to a nested Codex CLI session.  The
nested session is instructed to use the `$imagegen` skill and the built-in
`image_gen` tool, then save project-local PNGs and metadata under output/assets.

Usage:
  python3 scripts/run_stock_image_codex.py <slug>
  python3 scripts/run_stock_image_codex.py <slug> --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from report_contract_lib import (
    ASSET_DIR,
    ROOT,
    frontmatter_value,
    prohibited_image_generation_hits,
    read_markdown,
    rel,
    selected_image_path,
)


@dataclass(frozen=True)
class StagePaths:
    slug: str
    plan: Path
    research: Path
    draft: Path
    prompts: tuple[Path, Path, Path]
    images: tuple[Path, Path, Path]
    scores: tuple[Path, Path, Path]
    manifest: Path
    review: Path
    selected: Path


def paths_for(slug: str) -> StagePaths:
    return StagePaths(
        slug=slug,
        plan=ROOT / "plan" / f"{slug}.md",
        research=ROOT / "research" / f"{slug}.md",
        draft=ROOT / "drafts" / f"{slug}.md",
        prompts=tuple(ASSET_DIR / f"{slug}-hero-v{i}.prompt.txt" for i in range(1, 4)),  # type: ignore[arg-type]
        images=tuple(ASSET_DIR / f"{slug}-hero-v{i}.png" for i in range(1, 4)),  # type: ignore[arg-type]
        scores=tuple(ASSET_DIR / f"{slug}-hero-v{i}.score.json" for i in range(1, 4)),  # type: ignore[arg-type]
        manifest=ASSET_DIR / f"{slug}-image-manifest.json",
        review=ASSET_DIR / f"{slug}-image-review.txt",
        selected=ASSET_DIR / f"{slug}-selected-image.json",
    )


def require_inputs(paths: StagePaths) -> None:
    missing = [p for p in (paths.plan, paths.research, paths.draft) if not p.is_file()]
    if missing:
        missing_list = ", ".join(rel(p) for p in missing)
        raise SystemExit(f"필수 선행 산출물 없음: {missing_list}")


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        match = re.match(r"\A---\s*\r?\n.*?\r?\n---\s*(?:\r?\n)?", text, re.DOTALL)
        if match:
            return text[match.end() :]
    return text


def _first_h1(body: str) -> str:
    match = re.search(r"^#(?!#)\s+(.+?)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _section(body: str, title: str, max_chars: int = 900) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(title)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(body)
    if not match:
        return ""
    return _squash(match.group("body"), max_chars=max_chars)


def _squash(text: str, *, max_chars: int) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"\[[A-Z]\d+\]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def load_context(paths: StagePaths) -> dict[str, str]:
    plan_fm, plan_body, _plan_raw, plan_text = read_markdown(paths.plan)
    research_fm, research_body, _research_raw, research_text = read_markdown(paths.research)
    draft_fm, draft_body, _draft_raw, draft_text = read_markdown(paths.draft)

    title = (
        frontmatter_value(draft_fm, "title")
        or _first_h1(draft_body)
        or frontmatter_value(research_fm, "title")
        or frontmatter_value(plan_fm, "topic")
        or paths.slug
    )
    subtitle = frontmatter_value(draft_fm, "subtitle") or frontmatter_value(plan_fm, "topic")
    ticker = frontmatter_value(draft_fm, "ticker") or frontmatter_value(plan_fm, "ticker")
    period_start = frontmatter_value(draft_fm, "period_start") or frontmatter_value(plan_fm, "period_start")
    period_end = frontmatter_value(draft_fm, "period_end") or frontmatter_value(plan_fm, "period_end")

    overview = _section(draft_body, "개요")
    mechanism = _section(draft_body, "메커니즘")
    impact = _section(draft_body, "영향과 적용")
    conclusion_tone = _squash(" ".join(part for part in (overview, impact) if part), max_chars=1000)
    research_summary = _squash(_strip_frontmatter(research_text), max_chars=1200)
    plan_summary = _squash(_strip_frontmatter(plan_text), max_chars=900)

    return {
        "slug": paths.slug,
        "title": title,
        "subtitle": subtitle,
        "ticker": ticker,
        "period": f"{period_start} ~ {period_end}".strip(" ~"),
        "overview": overview,
        "mechanism": mechanism,
        "impact": impact,
        "conclusion_tone": conclusion_tone,
        "research_summary": research_summary,
        "plan_summary": plan_summary,
        "plan_path": rel(paths.plan),
        "research_path": rel(paths.research),
        "draft_path": rel(paths.draft),
    }


def render_candidate_prompt(context: dict[str, str], variant: int) -> str:
    compositions = {
        1: (
            "sector-mechanism close-up",
            "A premium editorial macro scene built from abstract company/sector-relevant materials, "
            "showing the operating mechanism behind the report: supply, product cycle, demand, and risk in one restrained composition.",
        ),
        2: (
            "market-forces landscape",
            "A cinematic institutional-research hero visual where market currents, capital flow, and industry catalysts are implied through light, depth, and geometry, not literal charts.",
        ),
        3: (
            "risk-opportunity balance",
            "A balanced visual metaphor with tension between growth optionality and execution or macro risk, using contrast, layered materials, and calm studio lighting.",
        ),
    }
    label, composition = compositions[variant]
    return f"""Use case: stylized-concept
Asset type: 16:9 hero image for an HTML Korean stock/economy report
Report title: {context['title']}
Report subtitle: {context['subtitle']}
Ticker/company/sector context: {context['ticker']}
Requested period: {context['period']}
Composition concept: {label}
Primary request: {composition}
Report message to reflect: {context['conclusion_tone'] or context['overview']}
Mechanism cues: {context['mechanism']}
Impact/risk cues: {context['impact']}
Style: premium editorial finance illustration, abstract but concrete, high-end magazine opening image, sophisticated depth, realistic materials, cinematic studio lighting, restrained color palette, no hype.
Hard avoid: no visible text, no numbers, no ticker symbols, no company logo, no watermark, no UI screenshot, no fake dashboard, no readable chart labels, no buy/sell signal, no cartoon mascot.
Output requirement: save a PNG candidate exactly at output/assets/{context['slug']}-hero-v{variant}.png.
""".strip() + "\n"


def write_prompt_files(paths: StagePaths, context: dict[str, str]) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for variant, prompt_path in enumerate(paths.prompts, 1):
        prompt_path.write_text(render_candidate_prompt(context, variant), encoding="utf-8")


def render_codex_prompt(paths: StagePaths, context: dict[str, str]) -> str:
    prompt_paths = "\n".join(f"- {rel(path)}" for path in paths.prompts)
    image_paths = "\n".join(f"- {rel(path)}" for path in paths.images)
    score_paths = "\n".join(f"- {rel(path)}" for path in paths.scores)
    return f"""$imagegen

You are the Codex CLI image-generation executor for stock-report-harness `/stock-image {paths.slug}`.

Goal: generate three real PNG hero image candidates with the Codex `imagegen` skill / built-in `image_gen` tool, then write the stock-image metadata files. Do not create placeholders or procedural stand-ins.

Repository root: {ROOT}
Input files you must read before finalizing images:
- {context['plan_path']}
- {context['research_path']}
- {context['draft_path']}

Report context summary (use the files above as source of truth):
- title: {context['title']}
- subtitle: {context['subtitle']}
- ticker/company/sector: {context['ticker']}
- period: {context['period']}
- overview: {context['overview']}
- mechanism: {context['mechanism']}
- impact/tone: {context['impact']}

Prompt files already prepared; you may refine them only if doing so better reflects the report while preserving the hard avoid rules:
{prompt_paths}

Required PNG outputs, exactly these workspace paths:
{image_paths}

Required score JSON outputs:
{score_paths}
Each score JSON must be an object with: slug, candidate, image_path, prompt_path, report_fit, company_sector_fit, visual_clarity, premium_quality, restraint, total, notes.

Also write:
- {rel(paths.review)}: short image-review text explaining the selected candidate.
- {rel(paths.manifest)}: object with status "complete", generation_method "codex-cli-imagegen", generated_with "Codex CLI $imagegen / built-in image_gen", candidates, selected, and any source_image path if available.
- {rel(paths.selected)}: object containing at least slug, selected_candidate, image_path, reason, generated_with.

Hard image rules:
- No visible text, numbers, ticker symbols, logos, watermarks, UI screenshots, fake dashboards, or buy/sell signals.
- Use abstract/editorial visuals that match the actual report tone, including risks and uncertainty.
- Do not use local drawing/procedural/Pillow/SVG placeholder generation as a substitute for imagegen.
- Do not call direct LLM/OpenAI API keys and do not use browser-use.
- Because this asset is project-bound, copy/move the generated images from $CODEX_HOME/generated_images (if that is where the tool saves them) into the required workspace paths. Never leave a project-referenced asset only in $CODEX_HOME.

If the imagegen tool is unavailable or generation fails, write {rel(paths.manifest)} with status "blocked" and a concrete blocked_reason, keep the prompt files, do not create fake PNGs, and do not write a selected-image JSON that points to a nonexistent file.

Before finishing, verify the required PNGs and JSON files exist, then report the selected image path and any validation gaps.
"""


def codex_command(codex_bin: str, output_last_message: Path) -> list[str]:
    return [
        codex_bin,
        "-C",
        str(ROOT),
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
        "exec",
        "-o",
        str(output_last_message),
        "-",
    ]


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return rel(value)
    return str(value)


def write_blocked_manifest(paths: StagePaths, *, reason: str, command: list[str] | None = None) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": paths.slug,
        "status": "blocked",
        "generation_method": "codex-cli-imagegen",
        "generated_with": "Codex CLI $imagegen / built-in image_gen",
        "blocked_reason": reason,
        "prompt_files": [rel(p) for p in paths.prompts],
        "required_images": [rel(p) for p in paths.images],
        "required_scores": [rel(p) for p in paths.scores],
        "codex_command": shlex.join(command) if command else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    paths.manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def write_in_progress_manifest(paths: StagePaths, *, command: list[str]) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": paths.slug,
        "status": "in_progress",
        "generation_method": "codex-cli-imagegen",
        "generated_with": "Codex CLI $imagegen / built-in image_gen",
        "prompt_files": [rel(p) for p in paths.prompts],
        "required_images": [rel(p) for p in paths.images],
        "required_scores": [rel(p) for p in paths.scores],
        "codex_command": shlex.join(command),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    paths.manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def verify_outputs(paths: StagePaths) -> list[str]:
    missing: list[str] = []
    for path in (*paths.prompts, *paths.images, *paths.scores, paths.manifest, paths.review, paths.selected):
        if not path.is_file():
            missing.append(rel(path))
    for score in paths.scores:
        if score.is_file():
            try:
                payload = json.loads(score.read_text(encoding="utf-8"))
            except Exception as exc:
                missing.append(f"{rel(score)} (invalid JSON: {exc})")
                continue
            if not isinstance(payload, dict):
                missing.append(f"{rel(score)} (JSON object required)")
    if paths.manifest.is_file():
        try:
            manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            missing.append(f"{rel(paths.manifest)} (invalid JSON: {exc})")
        else:
            if not isinstance(manifest, dict):
                missing.append(f"{rel(paths.manifest)} (JSON object required)")
            elif manifest.get("status") != "complete":
                reason = manifest.get("blocked_reason") or f"status {manifest.get('status')!r}"
                missing.append(f"{rel(paths.manifest)} ({reason})")
            else:
                if manifest.get("generation_method") != "codex-cli-imagegen":
                    missing.append(f"{rel(paths.manifest)} (generation_method must be codex-cli-imagegen)")
                if not str(manifest.get("generated_with") or "").strip():
                    missing.append(f"{rel(paths.manifest)} (generated_with required)")
                prohibited = prohibited_image_generation_hits(manifest)
                if prohibited:
                    missing.append(f"{rel(paths.manifest)} (prohibited generation metadata: {'; '.join(prohibited[:3])})")
    if paths.selected.is_file():
        try:
            selected_payload = json.loads(paths.selected.read_text(encoding="utf-8"))
        except Exception as exc:
            missing.append(f"{rel(paths.selected)} (invalid JSON: {exc})")
        else:
            if not isinstance(selected_payload, dict):
                missing.append(f"{rel(paths.selected)} (JSON object required)")
            else:
                prohibited = prohibited_image_generation_hits(selected_payload)
                if prohibited:
                    missing.append(f"{rel(paths.selected)} (prohibited generation metadata: {'; '.join(prohibited[:3])})")
    selected_path, _payload = selected_image_path(paths.slug)
    if selected_path is None:
        missing.append(f"{rel(paths.selected)} (image_path not resolvable)")
    elif not selected_path.is_file():
        missing.append(f"{rel(selected_path)} (selected PNG missing)")
    elif selected_path.suffix.lower() != ".png":
        missing.append(f"{rel(selected_path)} (selected image must be PNG)")
    return missing


def run_codex(cmd: list[str], prompt: str, log_path: Path, *, timeout_seconds: int) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timeout = None if timeout_seconds <= 0 else timeout_seconds
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        cwd=ROOT,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    log_path.write_text(
        "# Command\n"
        + shlex.join(cmd)
        + "\n\n# STDOUT\n"
        + proc.stdout
        + "\n\n# STDERR\n"
        + proc.stderr,
        encoding="utf-8",
    )
    return proc.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Report slug, e.g. samsung-electronics-recent-30d-2026-05")
    parser.add_argument("--codex-bin", default=os.environ.get("STOCK_IMAGE_CODEX_BIN", "codex"), help="Codex CLI executable")
    parser.add_argument("--timeout-seconds", type=int, default=3600, help="Codex CLI timeout; 0 disables timeout")
    parser.add_argument("--dry-run", action="store_true", help="Print the Codex command and prompt without writing or running")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = paths_for(args.slug)
    require_inputs(paths)
    context = load_context(paths)
    prompt = render_codex_prompt(paths, context)
    logs_dir = ROOT / ".omx" / "logs"
    output_last_message = logs_dir / f"stock-image-{args.slug}-codex-last-message.md"
    log_path = logs_dir / f"stock-image-{args.slug}-codex-cli.log"
    cmd = codex_command(args.codex_bin, output_last_message)

    if args.dry_run:
        print("# Codex command")
        print(shlex.join(cmd))
        print("\n# Prepared prompt files")
        for variant in range(1, 4):
            print(f"## {rel(paths.prompts[variant - 1])}\n{render_candidate_prompt(context, variant)}")
        print("\n# Codex prompt")
        print(prompt)
        return 0

    write_prompt_files(paths, context)
    write_in_progress_manifest(paths, command=cmd)

    if not shutil.which(args.codex_bin):
        reason = f"Codex CLI executable not found: {args.codex_bin!r}"
        write_blocked_manifest(paths, reason=reason, command=cmd)
        print(f"[BLOCKED] {reason}", file=sys.stderr)
        return 2

    try:
        returncode = run_codex(cmd, prompt, log_path, timeout_seconds=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        reason = f"Codex CLI timed out after {args.timeout_seconds} seconds"
        write_blocked_manifest(paths, reason=reason, command=cmd)
        print(f"[BLOCKED] {reason}", file=sys.stderr)
        return 2

    if returncode != 0:
        reason = f"Codex CLI exited with status {returncode}; see {rel(log_path)}"
        write_blocked_manifest(paths, reason=reason, command=cmd)
        print(f"[BLOCKED] {reason}", file=sys.stderr)
        return returncode or 1

    missing = verify_outputs(paths)
    if missing:
        reason = "Codex CLI finished but required stock-image outputs are missing/invalid: " + "; ".join(missing[:12])
        write_blocked_manifest(paths, reason=reason, command=cmd)
        print(f"[BLOCKED] {reason}", file=sys.stderr)
        return 2

    selected_path, _payload = selected_image_path(paths.slug)
    print(f"[PASS] stock-image generated via Codex CLI imagegen: {rel(selected_path) if selected_path else rel(paths.selected)}")
    print(f"  manifest: {rel(paths.manifest)}")
    print(f"  codex log: {rel(log_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
