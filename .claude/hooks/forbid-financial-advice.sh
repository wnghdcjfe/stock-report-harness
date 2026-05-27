#!/usr/bin/env bash
# Pre/PostToolUse: block prohibited investment-advice / guaranteed-return phrasing in drafts and final HTML.
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

def target(path: str) -> bool:
    path = path.replace('\\', '/')
    return (path.startswith('drafts/') and path.endswith('.md')) or (path.startswith('output/') and path.endswith('.html'))

patterns = [
    r'지금\s*사야\s*합니다', r'반드시\s*사(?:세요|야)', r'사야\s*합니다',
    r'매수\s*적기', r'매수\s*(?:추천|권장)', r'지금\s*매수',
    r'100\s*%\s*수익', r'확실한\s*수익', r'보장된\s*수익', r'수익\s*보장', r'무조건\s*수익',
    r'원금\s*손실\s*없음', r'원금\s*보장', r'리스크\s*없는',
    r'마지막\s*기회', r'지금\s*안\s*사면\s*후회', r'놓치면\s*후회',
    r'guaranteed\s+returns?', r'risk[-\s]?free\s+(?:profit|return|investment)', r'\bbuy\s+now\b', r'last\s+chance',
]
compiled = [(p, re.compile(p, re.I)) for p in patterns]

# PreToolUse can inspect proposed Write/Edit strings. PostToolUse scans actual files.
candidates: dict[str, str] = {}
path_value = ti.get('file_path') or ti.get('path')
if isinstance(path_value, str):
    rp = relpath(path_value)
    if target(rp):
        for key in ('content', 'new_string'):
            value = ti.get(key)
            if isinstance(value, str) and value:
                candidates[f'{rp} (proposed {key})'] = value
        edits = ti.get('edits')
        if isinstance(edits, list):
            combined = '\n'.join(str(e.get('new_string') or '') for e in edits if isinstance(e, dict))
            if combined:
                candidates[f'{rp} (proposed edits)'] = combined
        file_path = root / rp
        if file_path.is_file():
            try:
                candidates[rp] = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                pass

# If the hook was invoked after a Bash/build operation, scan all report targets but keep it bounded.
if tool == 'Bash':
    for glob in ('drafts/*.md', 'output/*.html'):
        for path in root.glob(glob):
            try:
                candidates[path.relative_to(root).as_posix()] = path.read_text(encoding='utf-8')
            except Exception:
                continue

def negated_or_policy_context(text: str, start: int, end: int) -> bool:
    line_start = text.rfind('\n', 0, start) + 1
    line_end = text.find('\n', end)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    # Allow disclaimers or policy sentences that explicitly reject/forbid the phrase.
    return bool(re.search(r'(아닙니다|아님|하지\s*않|목적으로\s*하지|금지|차단|피해야|사용하지\s*않|not\s+(?:investment\s+)?advice|not\s+guarantee)', line, re.I))

findings = []
for name, text in candidates.items():
    for label, rx in compiled:
        m = rx.search(text)
        while m and negated_or_policy_context(text, m.start(), m.end()):
            m = rx.search(text, m.end())
        if m:
            findings.append((name, m.group(0)))
            break

if findings:
    preview = '; '.join(f'{name}: "{match}"' for name, match in findings[:5])
    reason = '투자 권유/수익 보장/FOMO 금지 표현을 차단합니다. ' + preview
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(2)
PY
exit $?
