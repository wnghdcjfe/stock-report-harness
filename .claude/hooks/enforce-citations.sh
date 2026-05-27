#!/usr/bin/env bash
# Pre/PostToolUse: ensure numeric claims in drafts carry source markers.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# shellcheck source=/dev/null
. "$ROOT/.claude/hooks/lib/guardrail-common.sh" 2>/dev/null || exit 0
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"
trap 'rm -f "$TMP_INPUT"' EXIT

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
raw = Path(sys.argv[2]).read_text(encoding="utf-8", errors="ignore")
try:
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    data = {}

tool = data.get('tool_name') or ''
ti = data.get('tool_input') or {}

def relpath(value: str) -> str:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = root / p
    try:
        return p.resolve().relative_to(root).as_posix()
    except Exception:
        return p.resolve().as_posix()

paths = []
path_value = ti.get('file_path') or ti.get('path')
if isinstance(path_value, str):
    rp = relpath(path_value)
    if rp.startswith('drafts/') and rp.endswith('.md'):
        paths.append(root / rp)
if tool == 'Bash':
    # Bounded scan: only existing drafts. This catches generated/rewritten drafts.
    paths.extend(sorted((root / 'drafts').glob('*.md')))

source_marker = re.compile(r'\[(?:S|N|P|H|A|F|R)\d+\]', re.I)
numberish = re.compile(r'(?<![A-Za-z])(?:[$₩€¥]\s*\d[\d,]*(?:\.\d+)?\s*(?:B|M|K|bn|mn)?|\d[\d,]*(?:\.\d+)?\s*(?:%|원|달러|억원|조원|억|조|만|배|주|건|개|명|분기|B|M|K|bn|mn))(?![A-Za-z])', re.I)
url_or_ref = re.compile(r'https?://|References\b|^\s*-\s*\[(?:S|N|P|H|A|F|R)\d+\]', re.I)

# Lines/blocks where digits are structural rather than factual claims.
def check_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    findings = []
    in_fm = False
    fm_seen = False
    in_code = False
    in_refs = False
    for idx, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if idx == 1 and stripped == '---':
            in_fm = True; fm_seen = True; continue
        if in_fm:
            if stripped == '---':
                in_fm = False
            continue
        if stripped.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r'^##\s+References\s*$', stripped, re.I):
            in_refs = True
            continue
        if in_refs:
            continue
        if not stripped or stripped.startswith('#') or re.match(r'^\|?\s*:?-{3,}', stripped):
            continue
        if re.match(r'^(label|title|tone|aria_label|aria-label|field|interval|currency|source):\s*', stripped, re.I):
            continue
        if stripped.startswith('<span class="word-cloud__term"') or stripped.startswith('<div class="word-cloud"') or stripped == '</div>':
            continue
        if not numberish.search(line):
            continue
        if source_marker.search(line) or url_or_ref.search(line):
            continue
        # Exempt pure markdown table formatting and pure dates inside linked titles are still claims, so not exempted.
        findings.append((idx, stripped[:180]))
        if len(findings) >= 8:
            break
    return findings

all_findings = []
seen = set()
for path in paths:
    if path in seen or not path.is_file():
        continue
    seen.add(path)
    findings = check_file(path)
    if findings:
        rel = path.relative_to(root).as_posix()
        for line_no, sample in findings:
            all_findings.append(f'{rel}:{line_no}: {sample}')

if all_findings:
    reason = 'draft 숫자 주장에는 [S1]/[N1]/[P1] 같은 출처 표식이 필요합니다. ' + ' | '.join(all_findings[:6])
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)
PY
exit $?
